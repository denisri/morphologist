import os
import glob

from morphologist.core.analysis import SharedPipelineAnalysis
from morphologist.core.subject import Subject
from capsul.process import get_process_instance
from capsul.process.process_with_fom import ProcessWithFom

# the following 4 lines are a hack to add /tmp to the FOM search path
# before it is used by StudyConfig
from soma.application import Application
soma_app = Application('capsul', plugin_modules=['soma.fom'])
soma_app.initialize()
soma_app.fom_manager.paths.append('/tmp')

fom_content = '''{
    "fom_name": "mock_fom",

    "formats": {
        "NIFTI": "nii",
        "NIFTI gz": "nii.gz"
    },
    "format_lists": {
        "images": ["NIFTI gz", "NIFTI"]
    },

    "shared_patterns": {
      "subject": "<group>-<subject>"
    },

    "processes": {
        "MyPipeline": {
            "input_image":
                [["input:{subject}_input", "images"]],
            "output_image":
                [["output:{subject}_output", "images"]],
        },
        "MyPipeline.node1": {
            "output_image": [["output:{subject}_node1_output", "images"]]
        },
        "MyPipeline.constant": {
            "output_image": [["output:{subject}_constant_output", "images"]]
        }
    }

}
'''
open('/tmp/mock_fom.json', 'w').write(fom_content)


class MockAnalysis(SharedPipelineAnalysis):

    def __init__(self, study):
        study.input_fom = 'mock_fom'
        study.output_fom = 'mock_fom'
        super(MockAnalysis, self).__init__(study)


    def _init_steps(self):
        self._steps = []

    def build_pipeline(self):
        return get_process_instance(
            'capsul.pipeline.test.test_pipeline.MyPipeline')

    def get_attributes(self, subject):
        attributes_dict = {
            'group': subject.groupname,
            'subject': subject.name,
        }
        return attributes_dict

    def set_parameters(self, subject):
        self.subject = subject
        super(MockAnalysis, self).set_parameters(subject)

    def import_data(self, subject):
        self.propagate_parameters()
        filename = self.pipeline.process.input_image
        open(filename, 'w').write('blah.\n')
        return filename


class MockFailedAnalysis(MockAnalysis):

    pass


def main():
    import sys
    import time
    import optparse

    parser = optparse.OptionParser()
    parser.add_option('-f', '--fail', action='store_true',
                      dest="fail", default=False, 
                      help="Execute only this test function.")
    options, args = parser.parse_args(sys.argv)

    time_to_sleep = int(args[1])
    args = args[2:]

    for filename in args:
        fd = open(filename, "w")
        fd.close()
    time.sleep(time_to_sleep)

    if options.fail:
        sys.exit(1)

if __name__ == '__main__' : main()
