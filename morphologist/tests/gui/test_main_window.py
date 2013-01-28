import sys
import unittest
import os

from morphologist.study import Subject, Study
from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui.main_window import create_main_window
from morphologist.tests.gui import TestGui
from morphologist.tests.gui.test_study_editor_widget import TestStudyGui
from morphologist.tests.intra_analysis.study import IntraAnalysisStudyTestCase
from morphologist.tests.study import MockStudyTestCase


class TestStudyWidget(TestGui):

    def __init__(self, *args, **kwargs):
        super(TestStudyWidget, self).__init__(*args, **kwargs)

    def setUp(self):
        self.test_case = self._create_test_case()
        if not os.path.exists(self.test_case.outputdir):
            os.makedirs(self.test_case.outputdir)


    def _create_test_case(self):
        raise NotImplementedError('TestStudyWidget is an abstract class')

    @TestGui.start_qt_and_test
    def test_start_main_window(self):
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.set_parameters()
        self.test_case.study.clear_results()
        main_window = create_main_window()
        self.keep_widget_alive(main_window)
        main_window.set_study(self.test_case.study)
        main_window.show()
        model = main_window.study_tablemodel
        subjects = [model.data(model.index(i, 0)) \
                        for i in range(model.rowCount())]
        subjects = sorted(subjects)
        main_window.close()
        self.assertEqual(self.test_case.study.subjects, subjects)

    @TestGui.start_qt_and_test
    def test_create_new_study(self):
        main_window = create_main_window()
        self.keep_widget_alive(main_window)
        main_window.show()
        QtTest.QTest.keyClicks(main_window, "n", QtCore.Qt.ControlModifier, 10 )
                                    
        dialog = main_window.findChild(QtGui.QDialog, 'StudyEditorDialog')
        print "dialog : ", dialog
        TestStudyGui.action_define_new_study_content(dialog, 
                                                     self.test_case.studyname, 
                                                     self.test_case.outputdir,
                                                     self.test_case.filenames)
        self.assertEqual(main_window.study.name, self.test_case.studyname)
        self.assertEqual(main_window.study.outputdir, self.test_case.outputdir)
        self._assert_subjects_exist(main_window.study)
        main_window.close()
        
    def _assert_subjects_exist(self, study):
        for filename in self.test_case.filenames:
            subject = Subject(Study.DEFAULT_GROUP, 
                              Study.define_subjectname_from_filename(filename), 
                              filename)
            self.assert_(subject in study.subjects)
            subject_index = study.subjects.index(subject)
            study_subject = study.subjects[subject_index]
            self.assert_(os.path.exists(study_subject.filename))
            self.assert_(study_subject.filename.startswith(self.test_case.outputdir))


class TestStudyWidgetIntraAnalysis(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestStudyWidgetIntraAnalysis, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = IntraAnalysisStudyTestCase()
        return test_case


class TestMockStudyWidget(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestMockStudyWidget, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = MockStudyTestCase()
        return test_case


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudyWidgetIntraAnalysis)
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMockStudyWidget))
    unittest.TextTestRunner(verbosity=2).run(suite)

