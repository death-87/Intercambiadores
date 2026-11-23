import unittest
from unittest.mock import Mock,patch
from piping_projects import call,configured


class ProjectServiceTests(unittest.TestCase):
    def setUp(self):self.config={'PIPING_PROJECTS_URL':'https://script.google.com/macros/s/test/exec','PIPING_PROJECTS_TOKEN':'private-test-token','PIPING_PROJECTS_PASSWORD':'private-password'}

    def test_requires_configuration(self):
        self.assertFalse(configured({}))
        with self.assertRaises(ValueError):call({},'list')

    def test_save_response_and_revision(self):
        response=Mock();response.json.return_value={'ok':True,'project':{'id':'abc','revision':2,'name':'Equipo piping'}}
        with patch('piping_projects.requests.post',return_value=response) as post:
            result=call(self.config,'save',name='Equipo piping',design={'version':1,'components':[]},revision=1)
        self.assertEqual(result['project']['revision'],2)
        self.assertEqual(post.call_args.kwargs['json']['revision'],1)
        self.assertEqual(post.call_args.kwargs['json']['token'],'private-test-token')
        self.assertNotIn('PIPING_PROJECTS_PASSWORD',post.call_args.kwargs['json'])

    def test_service_error(self):
        response=Mock();response.json.return_value={'ok':False,'error':'Versión más reciente'}
        with patch('piping_projects.requests.post',return_value=response),self.assertRaisesRegex(ValueError,'Versión más reciente'):call(self.config,'save')


if __name__=='__main__':unittest.main()
