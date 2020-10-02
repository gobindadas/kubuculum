
import logging
import os
import subprocess
from kubuculum import util_functions
from kubuculum import k8s_wrappers

logger = logging.getLogger (__name__)

class server_fio:

    def __init__ (self, run_dir, params_dict, globals):

        # get directory pathname for module
        self.dirpath = os.path.dirname (os.path.abspath (__file__))

        # output directory for self
        self.tag = 'server_fio' # TODO: make it unique

        # load defaults from file
        yaml_file = self.dirpath + '/defaults.yaml'
        self.params = util_functions.dict_from_file (yaml_file)

        # update params
        labels_path = ['server_fio']
        new_params = util_functions.get_modparams (params_dict, labels_path)
        util_functions.deep_update (self.params, new_params)
        util_functions.update_modparams (self.params, globals)
        self.params['dir'] = run_dir + '/' + self.tag

        # parameters clients need in order to use this object
        self.returnparams = {}
        self.returnparams['datadir'] = self.params['datadir']
        self.returnparams['serverlist'] = [] # populated at start

    # start: create StatefulSet
    def start (self, passed_params):

        logger.debug (f'server_fio start')
        util_functions.deep_update (self.params, passed_params)
        logger.debug (f'server_fio parameters: {self.params}')

        # create directory for self
        util_functions.create_dir (self.params['dir'])

        templates_dir = self.dirpath + '/' + self.params['templates_dir']
        template_file = self.params['template_file']
        yaml_file = self.params['dir'] + '/' + self.params['yaml_file']

        util_functions.instantiate_template ( templates_dir, \
            template_file, yaml_file, self.params)

        logger.debug (f'starting server_fio pods')
        # create the pods
        # expected count is nservers
        # set retries to nservers with pause of 30 sec
        # timeout of 300 sec; TODO: use a param here
        k8s_wrappers.createpods_sync (self.params['namespace'], \
            yaml_file, self.params['podlabel'], \
            self.params['nservers'], 30, self.params['nservers'], 300)
        logger.debug (f'server_fio pods ready')

        # TODO: use list of pods as returned by k8s
        # update returnparams with server list
        for inst in range (self.params['nservers']):
            new_elem = 'server-fio-' + str (inst) + '.server-fio'
            self.returnparams['serverlist'].append (new_elem)

        return self.returnparams


    # stop operation: delete StatefulSet and PVCs
    def stop (self):

        namespace = self.params['namespace']
        yaml_file = self.params['dir'] + '/' + self.params['yaml_file']

        # delete the pods
        k8s_wrappers.deletefrom_yaml (yaml_file, namespace)

        # delete the PVCs
        k8s_wrappers.deletefrom_label (namespace, \
            self.params['podlabel'], "pvc")


