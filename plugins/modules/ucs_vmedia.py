#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: ucs_vmedia
short_description: Configures a vMedia policy on Cisco UCS Central
description:
- Configures VLANs on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify VLANs are present and will create if needed.
    - If C(absent), will verify VLANs are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name assigned to the VLAN.
    - The VLAN name is case sensitive.
    - This name can be between 1 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the VLAN is created.
    required: yes
  multicast_policy:
    description:
    - The multicast policy associated with this VLAN.
    - This option is only valid if the Sharing Type field is set to None or Primary.
    default: ''
  fabric:
    description:
    - "The fabric configuration of the VLAN.  This can be one of the following:"
    - "common - The VLAN applies to both fabrics and uses the same configuration parameters in both cases."
    - "A — The VLAN only applies to fabric A."
    - "B — The VLAN only applies to fabric B."
    - For upstream disjoint L2 networks, Cisco recommends that you choose common to create VLANs that apply to both fabrics.
    choices: [common, A, B]
    default: common
  id:
    description:
    - The unique string identifier assigned to the VLAN.
    - A VLAN ID can be between '1' and '3967', or between '4048' and '4093'.
    - You cannot create VLANs with IDs from 4030 to 4047. This range of VLAN IDs is reserved.
    - The VLAN IDs you specify must also be supported on the switch that you are using.
    - VLANs in the LAN cloud and FCoE VLANs in the SAN cloud must have different IDs.
    - Optional if state is absent.
    required: yes
  sharing:
    description:
    - The Sharing Type field.
    - "Whether this VLAN is subdivided into private or secondary VLANs. This can be one of the following:"
    - "none - This VLAN does not have any secondary or private VLANs. This is a regular VLAN."
    - "primary - This VLAN can have one or more secondary VLANs, as shown in the Secondary VLANs area. This VLAN is a primary VLAN in the private VLAN domain."
    - "isolated - This is a private VLAN associated with a primary VLAN. This VLAN is an Isolated VLAN."
    - "community - This VLAN can communicate with other ports on the same community VLAN as well as the promiscuous port. This VLAN is a Community VLAN."
    choices: [none, primary, isolated, community]
    default: none
  native:
    description:
    - Designates the VLAN as a native VLAN.
    choices: ['yes', 'no']
    default: 'no'
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure VLAN
  ucs_vlans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vlan2
    id: '2'
    native: 'yes'

- name: Remove VLAN
  ucs_vlans:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vlan2
    state: absent
'''

RETURN = r'''
#
'''
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cwilloughby_bw.ucsc.plugins.module_utils.ucs import UCSModule, ucs_argument_spec

def main():

    vmedia_entry_spec = dict(
        auth_option=dict(type='str', default='none', choices=["default", "none", "ntlm", "ntlmi", "ntlmssp", "ntlmsspi", "ntlmv2", "ntlmv2i"]),
        description=dict(type='str', default=''),
        device_type=dict(type='str', required=True, choices=["cdd", "hdd", "unknown"]),
        image_file_name=dict(type='str'),
        image_name_variable=dict(type='str', default='none', choices=["none", "service-profile-name"]),
        image_path=dict(type='str'),
        mapping_name=dict(type='str', required=True),
        mount_protocol=dict(type='str', default='http', choices=["cifs", "http", "https", "nfs", "unknown"]),
        password=dict(type='str'),
        remote_host=dict(type='str'),
        remote_ip=dict(type='str'),
        remote_port=dict(type='int'),
        user_id=dict(type='str')
    )

    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str', required=True),
        description=dict(type='str', default=''),
        retry_on_mount_fail=dict(type='str',default='yes', choices=['yes', 'no']),
        vmedia_entries=dict(type='list', elements='dict', options=vmedia_entry_spec),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['name']],
        ],
    )
    ucs = UCSModule(module)

    err = False

    # UCSModule creation above verifies ucscsdk is present and exits on failure, so additional imports are done below.
    from ucscsdk.mometa.cimcvmedia.CimcvmediaMountConfigPolicy import CimcvmediaMountConfigPolicy
    from ucscsdk.mometa.cimcvmedia.CimcvmediaConfigMountEntry import CimcvmediaConfigMountEntry

    changed = False
    try:
        mo_exists = False
        props_match = False
        dn = module.params['org_dn'] + '/mnt-cfg-policy-' + module.params['name']

        mo = ucs.login_handle.query_dn(dn)
        if mo:
            mo_exists = True

        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if mo_exists:
                if not module.check_mode:
                    ucs.login_handle.remove_mo(mo)
                    ucs.login_handle.commit()
                changed = True
        else:
            if mo_exists:
                # check top-level mo props
                kwargs = dict(name=module.params['name'])
                kwargs['descr'] = module.params['description']
                kwargs['retry_on_mount_fail'] = module.params['retry_on_mount_fail']
                # check vmedia entries match
                print(module.params['vmedia_entries'])
                # derp = ucs.login_handle.query_children(mo)
                # for vmedia_entry in module.params['vmedia_entries']:
                    # print('hello world')
                    # entry = ucs.login_handle.query_dn(dn+"/cfg-mnt-entry-"+vmedia_entry['mapping_name'])
                    # # print(dn+"/cfg-mnt-entry-"+vmedia_entry['mapping_name'])
                    # print(derp[vmedia_entry['mapping_name']])
                    # if(entry.check_prop_match(**vmedia_entry)):
                    #     match = True
                    # else:
                    #     match = False
                    # props_match_checks[vmedia_entry['mapping_name']] = match
                if (mo.check_prop_match(**kwargs)):
                    match = True
            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = CimcvmediaMountConfigPolicy(
                        parent_mo_or_dn=module.params['org_dn'],
                        name=module.params['name'],
                        descr=module.params['description'],
                        retry_on_mount_fail=module.params['retry_on_mount_fail'],
                    )
                    ucs.login_handle.add_mo(mo, True)
                    # for vmedia_entry in module.params['vmedia_entries']:
                    #     entry = CimcvmediaConfigMountEntry(parent_mo_or_dn=dn,**vmedia_entry)
                    #     ucs.login_handle.add_mo(entry, True)

                    
                    ucs.login_handle.commit()
                changed = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
