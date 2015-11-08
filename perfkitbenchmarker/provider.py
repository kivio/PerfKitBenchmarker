
class CloudProvider(object):

    def __init__(self, cloud):
        self._cloud = cloud

    def __import_child_class(self, base_class, module, default=None, get_all=False):
        if get_all:
            result = []
        try:
            classes = dir(self.module.__dict__[module])
            for klass in classes:
                if isinstance(klass, base_class):
                    if get_all:
                        result.append(klass)
                    else:
                        return klass
            if get_all:
                return result
        except KeyError:
            return default

    @staticmethod
    def get_list():
        import os
        return [provider for provider in os.listdir(
            os.path.join(os.path.dirname(__file__), 'providers')) if not provider.startswith('__')]

    @property
    def name(self):
        return self._cloud

    @property
    def module(self):
        import imp
        try:
            return imp.load_source(self._cloud, 'providers')
        except ImportError:
            raise ImportError('provider {} not found!'.format(self._cloud))

    @property
    def vm_classes(self):
        from perfkitbenchmarker.virtual_machine import BaseVirtualMachine
        return self.__import_child_class(BaseVirtualMachine, 'machine', [], get_all=True)

    @property
    def network(self):
        from perfkitbenchmarker.network import BaseNetwork
        return self.__import_child_class(BaseNetwork, 'network')

    @property
    def firewall(self):
        from perfkitbenchmarker.network import BaseFirewall
        return self.__import_child_class(BaseFirewall, 'network')

    @property
    def machine_spec(self):
        from perfkitbenchmarker.virtual_machine import BaseVmSpec
        return self.__import_child_class(BaseVmSpec, 'machine', BaseVmSpec)

    @property
    def disk_spec(self):
        from perfkitbenchmarker.disk import BaseDiskSpec
        return self.__import_child_class(BaseDiskSpec, 'disk', BaseDiskSpec)

    def create_vm(self, vm_spec, os_type, nets, firewalls):
        from perfkitbenchmarker import static_virtual_machine as static_vm
        from perfkitbenchmarker import errors

        vm = static_vm.StaticVirtualMachine.GetStaticVirtualMachine()
        if vm:
          return vm

        vm_classes = self.vm_classes
        if os_type not in vm_classes:
          raise errors.Error(
              'VMs of type %s" are not currently supported on cloud "%s".' %
              (os_type, self._cloud))
        vm_class = vm_classes[os_type]

        network = None
        if self.network:
            network = self.network.GetNetwork(vm_spec.zone, nets)

        firewall = None
        if self.firewall:
            firewall = self.firewall.GetFirewall(firewalls)

        return vm_class(vm_spec, network, firewall)