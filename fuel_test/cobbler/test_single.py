import unittest
from fuel_test.cobbler.vm_test_case import CobblerTestCase
from fuel_test.config import Config
from fuel_test.helpers import write_config
from fuel_test.manifest import Manifest, Template
from fuel_test.settings import CREATE_SNAPSHOTS, PUPPET_AGENT_COMMAND, ASTUTE_USE


class SingleTestCase(CobblerTestCase):
    def deploy(self):
        if ASTUTE_USE:
            self.prepare_astute()
            self.deploy_by_astute()
        else:
            self.prepare_only_site_pp()
            self.deploy_one_by_one()

    def deploy_one_by_one(self):
        self.validate(self.nodes().controllers[:1], PUPPET_AGENT_COMMAND)

    def deploy_by_astute(self):
        self.remote().check_stderr("astute -f /root/astute.yaml -v", True)

    def prepare_only_site_pp(self):
        manifest = Manifest().generate_openstack_manifest(
                template=Template.single(),
                ci=self.ci(),
                controllers=self.nodes().controllers,
                use_syslog=True,
                quantum=False, quantums=[],
                ha=False, ha_provider='generic',
                cinder=True, cinder_nodes=['all'], swift=False,
        )

        Manifest().write_manifest(remote=self.remote(), manifest=manifest)

    def prepare_astute(self):
        config = Config().generate(
            template=Template.single(),
            ci=self.ci(),
            nodes=[self.ci().nodes().controllers[:1]],
            quantum=False
        )
        print "Generated config.yaml:", config
        config_path = "/root/config.yaml"
        write_config(self.remote(), config_path, str(config))
        self.remote().check_call("cobbler_system -f %s" % config_path)
        self.remote().check_stderr("openstack_system -c %s -o /etc/puppet/manifests/site.pp -a /root/astute.yaml" % config_path, True)

    def test_single(self):
        self.deploy()

        if CREATE_SNAPSHOTS:
            self.environment().snapshot("single", force=True)

if __name__ == '__main__':
    unittest.main()
