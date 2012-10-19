import os
import os.path
import unittest


from steps import Step, Step1, Step2, Step3, IntraAnalysis
from steps import MissingInputFileError


class TestSteps(unittest.TestCase):

    def setUp(self):
        self.in_step_file_path = "/tmp/test_step_in"
        self.out_step_file_path = "/tmp/test_step_out"
        f = open(self.in_step_file_path, "w")
        f.close()
        self.in_analysis_file_path = "/tmp/test_analysis_in"
        self.out_analysis_file_path = "/tmp/test_analysis_out"
        f = open(self.in_analysis_file_path, "w")
        f.close()
        self.out_step1_file_path = "/tmp/test_step1_out"
        self.in_step2_file_path = "/tmp/test_step2_in"
        self.out_step2_file_path = "/tmp/test_step2_out"
        f = open(self.in_step2_file_path, "w")
        f.close()
        self.in_step3_file_path = "/tmp/test_step3_in"
        self.out_step3_file_path = "/tmp/test_step3_out"
        f = open(self.in_step3_file_path, "w")
        f.close()


    def test_run_step(self):
        step = Step()
        step.param_in = self.in_step_file_path
        step.param_out = self.out_step_file_path 
        step.run()
        self.assert_(os.path.isfile(step.param_out))
      

    def test_run_step_by_step(self):
        step1 = Step1()
        step1.param_in = self.in_analysis_file_path
        step1.param_out = self.out_step1_file_path
        step2 = Step2()
        step2.param_in_1 = self.in_step2_file_path
        step2.param_in_2 = self.out_step1_file_path
        step2.param_in_3 = 10
        step2.param_out = self.out_step2_file_path
        step3 = Step3()
        step3.param_in_1 = self.in_step3_file_path
        step3.param_in_2 = self.out_step2_file_path
        step3.param_out = self.out_step3_file_path

        step1.run()
        self.assert_(os.path.isfile(step1.param_out))
        step2.run()
        self.assert_(os.path.isfile(step2.param_out))
        step3.run()
        self.assert_(os.path.isfile(step3.param_out))


    def test_run_intra_analysis(self):
        intra_analysis = IntraAnalysis()
        intra_analysis.param_in = self.in_analysis_file_path
        intra_analysis.param_out = self.out_analysis_file_path
        intra_analysis.run()
        self.assert_(os.path.isfile(self.out_analysis_file_path))


    def test_raise_missing_in_file(self):
        os.remove(self.in_step_file_path)
        step = Step()
        step.param_in = self.in_step_file_path
        step.param_out = self.out_step_file_path
        self.assertRaises(MissingInputFileError, Step.run, step)


    def tearDown(self):
        if os.path.isfile(self.out_step_file_path):
            os.remove(self.out_step_file_path)
        if os.path.isfile(self.out_analysis_file_path):
            os.remove(self.out_analysis_file_path)
        if os.path.isfile(self.out_step1_file_path):
            os.remove(self.out_step1_file_path)
        if os.path.isfile(self.out_step2_file_path):
            os.remove(self.out_step2_file_path)
        if os.path.isfile(self.out_step3_file_path):
            os.remove(self.out_step3_file_path)



if __name__=="__main__":
    
    unittest.main()
