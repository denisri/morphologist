from optparse import OptionParser
import os

import brainvisa.axon
from brainvisa.processes import defaultContext
from brainvisa.configuration import neuroConfig
from soma import aims

from morphologist.steps import Step

class SpatialNormalization(Step):

    def __init__(self):
        super(SpatialNormalization, self).__init__()
        
        self.mri = None
        
        #outputs
        self.commissure_coordinates = None
        self.talairach_transform = None

    def get_command(self):
        # TODO 
        command = ['python', '-m', 'morphologist.intra_analysis_normalization', 
                   self.mri, 
                   self.commissure_coordinates, 
                   self.talairach_transform]
        return command
 
    @staticmethod
    def get_referential_uuid(image):
        vol = aims.read(image)
        return vol.header()["referential"]
        
    def run(self):
        print "Run spatial normalization on ", self.mri    
        brainvisa.axon.initializeProcesses()
        transformations_directory = os.path.dirname(self.talairach_transform)
        mri_name = os.path.basename(self.mri)
        mri_name = mri_name.split(".")[0]
        mri_path = os.path.dirname(self.mri)
        talairach_mni_transform = os.path.join(transformations_directory, 
                                               "RawT1_%s_TO_Talairach-MNI.trm" % mri_name)
        spm_transformation = os.path.join(mri_path, "%s_sn.mat" % mri_name)
        normalized_mri =  os.path.join(mri_path, "normalized_SPM_%s.nii" 
                                       % mri_name)
        defaultContext().runProcess("SPMnormalizationPipeline", self.mri, 
                                    talairach_mni_transform, 
                                    spm_transformation, normalized_mri)
        mri_referential = os.path.join(transformations_directory, 
                                       "RawT1-%s.referential" % mri_name)
        mri_referential_file = open(mri_referential, "w")
        mri_referential_file.write("attributes = {'uuid' : '%s'}" 
                                   % self.get_referential_uuid(self.mri))
        mri_referential_file.close()
        defaultContext().runProcess("TalairachTransformationFromNormalization", 
                                    talairach_mni_transform, 
                                    self.talairach_transform, 
                                    self.commissure_coordinates, 
                                    self.mri, mri_referential)
        brainvisa.axon.cleanup()
        return neuroConfig.exitValue
     
         
if __name__ == '__main__':
    
    parser = OptionParser(usage='%prog mri_file commissure_coordinates_file '
                          'talairach_transformation_file')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Invalid arguments : mri_file, commissure_coordinates_file'
                     ' and talairach_transformation_file are mandatory.')
    normalization = SpatialNormalization()
    normalization.mri = args[0]
    normalization.commissure_coordinates = args[1]
    normalization.talairach_transform = args[2]
    normalization.run()
