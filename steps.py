import os.path

class MissingInputFileError(Exception):
  pass

class Step(object):

    def __init__(self):
        self._in_file_params = ["param_in"]
        self._out_file_params = ["param_out"]


    def check_in_files(self):
        for in_file_param in self._in_file_params:
            in_file_name = getattr(self, in_file_param)
            if not os.path.isfile(in_file_name):
                raise MissingInputFileError(in_file_param)
            
    def run(self):
        self.check_in_files() 
        for out_file_param in self._out_file_params:
            out_file_name = getattr(self, out_file_param)
            out_file = open(out_file_name, "w")
            out_file.close()
  

class Step1(Step):
    pass


class Step2(Step):

    def __init__(self):
        super(Step2, self).__init__()
        self.param_in_1 = None
        self.param_in_2 = None
        self.param_in_3 = None
        self.param_out = None

        self._in_file_params = ["param_in_1", "param_in_2"]  
        self._out_file_params= ["param_out"]
   

class Step3(Step):

    def __init__(self):
        super(Step3, self).__init__()
        self.param_in_1 = None
        self.param_in_2 = None
        self.param_out = None

        self._in_file_params = ["param_in_1", "param_in_2"]  
        self._out_file_params= ["param_out"]


class IntraAnalysis(Step):
    pass 
