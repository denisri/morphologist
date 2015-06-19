import copy
import os
import shutil
import traits.api as traits

from morphologist.core.utils import OrderedDict
# CAPSUL
from capsul.pipeline import pipeline_tools
from capsul.process.process_with_fom import ProcessWithFom
# AIMS
from soma import aims

class AnalysisFactory(object):
    _registered_analyses = {}

    @classmethod
    def register_analysis(cls, analysis_type, analysis_class):
        cls._registered_analyses[analysis_type] = analysis_class

    @classmethod
    def create_analysis(cls, analysis_type, study):
        analysis_cls = cls.get_analysis_cls(analysis_type) 
        return analysis_cls(study)

    @classmethod
    def get_analysis_cls(cls, analysis_type):
        try:
            analysis_class = cls._registered_analyses[analysis_type]
            return analysis_class
        except KeyError:
            raise UnknownAnalysisError(analysis_type)


class UnknownAnalysisError(Exception):
    pass


class AnalysisMetaClass(type):

    def __init__(cls, name, bases, dct):
        AnalysisFactory.register_analysis(name, cls)
        super(AnalysisMetaClass, cls).__init__(name, bases, dct)


class Analysis(object):
    # XXX the metaclass automatically registers the Analysis class in the
    # AnalysisFactory and intializes the param_template_map
    __metaclass__ = AnalysisMetaClass

    def __init__(self, study):
        self._init_steps()
        self._init_step_ids()
        self.study = study
        self.pipeline = None  # should be a ProcessWithFom
        self.parameters = None

    def _init_steps(self):
        raise NotImplementedError("Analysis is an Abstract class.") 

    def _init_step_ids(self):
        self._step_ids = OrderedDict()
        for i, step in enumerate(self._steps):
            step_id = step.name  ##"%d_%s" % (i, step.name)
            self._step_ids[step_id] = step

    def step_from_id(self, step_id):
        return self._step_ids.get(step_id)

    def import_data(self, subject):
        raise NotImplementedError("Analysis is an Abstract class. import_data must be redefined.")

    def set_parameters(self, subject):
        raise NotImplementedError("Analysis is an Abstract class. set_parameters must be redefined.")

    def propagate_parameters(self):
        raise NotImplementedError("Analysis is an Abstract class. propagate_parameter must be redefined.") 

    def has_some_results(self):
        raise NotImplementedError("Analysis is an Abstract class. has_some_results must be redefined.")

    def has_all_results(self):
        raise NotImplementedError("Analysis is an Abstract class. has_all_results must be redefined.")

    def clear_results(self, step_ids=None):
        raise NotImplementedError("Analysis is an Abstract class. clear_results must be redefined.")

    def list_input_parameters_with_existing_files(self):
        pipeline = self.pipeline.process
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        param_names = [param_name
                       for param_name, trait
                          in pipeline.user_traits().iteritems()
                       if not trait.output
                          and (isinstance(trait.trait_type, traits.File)
                               or isinstance(trait.trait_type,
                                             traits.Directory)
                               or isinstance(trait.trait_type, traits.Any))]
        params = {}
        for param_name in param_names:
            value = getattr(pipeline, param_name)
            if isinstance(value, basestring) and os.path.exists(value):
                params[param_name] = value
        return params

    def list_output_parameters_with_existing_files(self):
        pipeline = self.pipeline.process
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        param_names = [param_name
                       for param_name, trait
                          in pipeline.user_traits().iteritems()
                       if trait.output
                          and (isinstance(trait.trait_type, traits.File)
                               or isinstance(trait.trait_type,
                                             traits.Directory)
                               or isinstance(trait.trait_type, traits.Any))]
        params = {}
        for param_name in param_names:
            value = getattr(pipeline, param_name)
            if isinstance(value, basestring) and os.path.exists(value):
                params[param_name] = value
        return params

        #existing =  pipeline_tools.nodes_with_existing_outputs(
            #self.pipeline.process)
        #params = []
        #for node_name, values in  existing.iteritems():
            #parmams.update(dict(values))
        #return params

    def convert_from_formats(self, old_volumes_format, old_meshes_format):
        def _convert_data(old_name, new_name):
            print 'converting:', old_name, 'to:', new_name
            data = aims.read(old_name)
            aims.write(data, new_name)
        def _remove_data(name):
            # TODO: use aims/somaio IO system for formats extensions
            exts = [['.nii'], ['.nii.gz'], ['.img', '.hdr'], ['.ima', '.dim'],
                    ['.dcm'], ['.mnc'],
                    ['.mesh'], ['.gii'], ['.ply']]
            for fexts in exts:
                for ext in fexts:
                    if name.endswith(ext):
                        basename =  name[:-len(ext)]
                        real_exts = fexts + [fexts[0] + '.minf']
                        for cext in real_exts:
                            filename = basename + cext
                            if os.path.isdir(filename):
                                print 'rmtree', filename
                                shutil.rmtree(filename)
                            elif os.path.exists(filename):
                                print 'rm', filename
                                os.unlink(filename)
        print 'convert analysis', self.subject, 'from formats:', old_volumes_format, old_meshes_format, 'to:', self.study.volumes_format, self.study.meshes_format
        if old_volumes_format == self.study.volumes_format \
                and old_meshes_format == self.study.meshes_format:
            print '    nothing to do.'
            return
        old_params = self.parameters
        # force re-running FOM
        self.set_parameters(self.subject)
        todo = [(old_params, self.parameters)]
        while todo:
            old_dict, new_dict = todo.pop(0)
            old_state = old_dict.get('state')
            new_state = new_dict.get('state', {})
            for key, value in old_state.iteritems():
                if isinstance(value, basestring) and os.path.exists(value):
                    new_value = new_state.get(key)
                    if new_value not in ('', None, traits.Undefined) \
                            and new_value != value:
                        _convert_data(value, new_value)
                    if new_value != value:
                        _remove_data(value)
            old_nodes = old_dict.get('nodes')
            new_nodes = new_dict.get('nodes', {})
            if old_nodes:
                todo += [(node, new_nodes.get(key, {}))
                         for key, node in old_nodes.iteritems()]


class SharedPipelineAnalysis(Analysis):
    '''
    An Analysis containing a capsul Pipeline instance, shared with other
    Analysis instances in the same study. The pipeline is wrapped in a
    ProcessWithFom.
    '''

    def __init__(self, study):
        super(SharedPipelineAnalysis, self).__init__(study)
        if study.template_pipeline is None:
            study.template_pipeline = ProcessWithFom(self.build_pipeline(),
                                                     study)
        # share the same instance of the pipeline to save memory and, most of
        # all, instantiation time
        self.pipeline = study.template_pipeline

    def build_pipeline(self):
        '''
        Returns
        -------
        pipeline: Pipeline instance
        '''
        raise NotImplementedError("SharedPipelineAnalysis is an Abstract class. build_pipeline must be redefined.")

    def set_parameters(self, subject):
        self.create_fom_completion(subject)

    def propagate_parameters(self):
        pipeline_tools.set_pipeline_state_from_dict(
            self.pipeline.process, self.parameters)

    def get_attributes(self, subject):
        raise NotImplementedError("SharedPipelineAnalysis is an Abstract class. get_attributes must be redefined.")

    def create_fom_completion(self, subject):
        pipeline = self.pipeline
        attributes_dict = self.get_attributes(subject)
        do_completion = False
        for attribute, value in attributes_dict.iteritems():
            if pipeline.attributes[attribute] != value:
                pipeline.attributes[attribute] = value
                do_completion = True
        if do_completion:
            #print 'create_completion for:', subject.id()
            pipeline.create_completion()
            self.parameters = pipeline_tools.dump_pipeline_state_as_dict(
                self.pipeline.process)
        #else: print 'skip completion for:', subject.id()

    def clear_results(self, step_ids=None):
        to_remove = self.existing_results(step_ids)
        print 'files to be removed:'
        print to_remove
        for filename in to_remove:
            filenames = self._files_for_format(filename)
            for f in filenames:
                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

    def _files_for_format(self, filename):
        ext_map = {
            'ima': ['ima', 'dim'],
            'img': ['img', 'hdr'],
            'arg': ['arg', 'data'],
        }
        ext_pos = filename.rfind('.')
        if ext_pos < 0:
            return [filename, filename + '.minf']
        ext = filename[ext_pos + 1:]
        exts = ext_map.get(ext, [ext])
        fname_base = filename[:ext_pos + 1]
        return [fname_base + ext for ext in exts] + [filename + '.minf']

    def existing_results(self, step_ids=None):
        pipeline = self.pipeline.process
        self.propagate_parameters()
        pipeline.enable_all_pipeline_steps()
        if step_ids:
            for pstep in pipeline.pipeline_steps.user_traits().keys():
                if pstep not in step_ids:
                    setattr(pipeline.pipeline_steps, pstep, False)
        outputs = pipeline_tools.nodes_with_existing_outputs(
            pipeline, recursive=True, exclude_inputs=True)
        existing = set()
        for node, item_list in outputs.iteritems():
            existing.update([filename for param, filename in item_list])
        # WARNING inputs may appear in outputs
        # (reorientation steps)
        for param_name, trait in pipeline.user_traits().iteritems():
            if not trait.output:
                value = getattr(pipeline, param_name)
                if isinstance(value, basestring) and value in existing:
                    existing.remove(value)
        return existing

    def has_some_results(self):
        return bool(self.existing_results())


class ImportationError(Exception):
    pass

