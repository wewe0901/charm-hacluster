# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import os
import sys
import tempfile
import unittest


mock_apt = mock.MagicMock()
sys.modules['apt_pkg'] = mock_apt
import hooks


@mock.patch.object(hooks, 'log', lambda *args, **kwargs: None)
@mock.patch('utils.COROSYNC_CONF', os.path.join(tempfile.mkdtemp(),
                                                'corosync.conf'))
class TestCorosyncConf(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    @mock.patch('pcmk.wait_for_pcmk')
    @mock.patch.object(hooks, 'peer_units')
    @mock.patch('pcmk.crm_opt_exists')
    @mock.patch.object(hooks, 'oldest_peer')
    @mock.patch.object(hooks, 'configure_corosync')
    @mock.patch.object(hooks, 'configure_cluster_global')
    @mock.patch.object(hooks, 'configure_monitor_host')
    @mock.patch.object(hooks, 'configure_stonith')
    @mock.patch.object(hooks, 'related_units')
    @mock.patch.object(hooks, 'get_cluster_nodes')
    @mock.patch.object(hooks, 'relation_set')
    @mock.patch.object(hooks, 'relation_ids')
    @mock.patch.object(hooks, 'get_corosync_conf')
    @mock.patch('pcmk.commit')
    @mock.patch.object(hooks, 'config')
    @mock.patch.object(hooks, 'parse_data')
    def test_ha_relation_changed(self, parse_data, config, commit,
                                 get_corosync_conf, relation_ids, relation_set,
                                 get_cluster_nodes, related_units,
                                 configure_stonith, configure_monitor_host,
                                 configure_cluster_global, configure_corosync,
                                 oldest_peer, crm_opt_exists, peer_units,
                                 wait_for_pcmk):
        crm_opt_exists.return_value = False
        oldest_peer.return_value = True
        related_units.return_value = ['ha/0', 'ha/1', 'ha/2']
        get_cluster_nodes.return_value = ['10.0.3.2', '10.0.3.3', '10.0.3.4']
        relation_ids.return_value = ['hanode:1']
        get_corosync_conf.return_value = True
        cfg = {'debug': False,
               'prefer-ipv6': False,
               'corosync_transport': 'udpu',
               'corosync_mcastaddr': 'corosync_mcastaddr',
               'cluster_count': 3}

        config.side_effect = lambda key: cfg.get(key)

        rel_get_data = {'locations': {'loc_foo': 'bar rule inf: meh eq 1'},
                        'clones': {'cl_foo': 'res_foo meta interleave=true'},
                        'groups': {'grp_foo': 'res_foo'},
                        'colocations': {'co_foo': 'inf: grp_foo cl_foo'},
                        'resources': {'res_foo': 'ocf:heartbeat:IPaddr2',
                                      'res_bar': 'ocf:heartbear:IPv6addr'},
                        'resource_params': {'res_foo': 'params bar'},
                        'ms': {'ms_foo': 'res_foo meta notify=true'},
                        'orders': {'foo_after': 'inf: res_foo ms_foo'}}

        def fake_parse_data(relid, unit, key):
            return rel_get_data.get(key, {})

        parse_data.side_effect = fake_parse_data

        hooks.ha_relation_changed()
        relation_set.assert_any_call(relation_id='hanode:1', ready=True)
        configure_stonith.assert_called_with()
        configure_monitor_host.assert_called_with()
        configure_cluster_global.assert_called_with()
        configure_corosync.assert_called_with()

        for kw, key in [('location', 'locations'),
                        ('clone', 'clones'),
                        ('group', 'groups'),
                        ('colocation', 'colocations'),
                        ('primitive', 'resources'),
                        ('ms', 'ms'),
                        ('order', 'orders')]:
            for name, params in rel_get_data[key].items():
                if name in rel_get_data['resource_params']:
                    res_params = rel_get_data['resource_params'][name]
                    commit.assert_any_call(
                        'crm -w -F configure %s %s %s %s' % (kw, name, params,
                                                             res_params))
                else:
                    commit.assert_any_call(
                        'crm -w -F configure %s %s %s' % (kw, name, params))

    @mock.patch.object(hooks, 'setup_maas_api')
    @mock.patch.object(hooks, 'validate_dns_ha')
    @mock.patch('pcmk.wait_for_pcmk')
    @mock.patch.object(hooks, 'peer_units')
    @mock.patch('pcmk.crm_opt_exists')
    @mock.patch.object(hooks, 'oldest_peer')
    @mock.patch.object(hooks, 'configure_corosync')
    @mock.patch.object(hooks, 'configure_cluster_global')
    @mock.patch.object(hooks, 'configure_monitor_host')
    @mock.patch.object(hooks, 'configure_stonith')
    @mock.patch.object(hooks, 'related_units')
    @mock.patch.object(hooks, 'get_cluster_nodes')
    @mock.patch.object(hooks, 'relation_set')
    @mock.patch.object(hooks, 'relation_ids')
    @mock.patch.object(hooks, 'get_corosync_conf')
    @mock.patch('pcmk.commit')
    @mock.patch.object(hooks, 'config')
    @mock.patch.object(hooks, 'parse_data')
    def test_ha_relation_changed_dns_ha(self, parse_data, config, commit,
                                        get_corosync_conf, relation_ids,
                                        relation_set, get_cluster_nodes,
                                        related_units, configure_stonith,
                                        configure_monitor_host,
                                        configure_cluster_global,
                                        configure_corosync, oldest_peer,
                                        crm_opt_exists, peer_units,
                                        wait_for_pcmk, validate_dns_ha,
                                        setup_maas_api):
        validate_dns_ha.return_value = True
        crm_opt_exists.return_value = False
        oldest_peer.return_value = True
        related_units.return_value = ['ha/0', 'ha/1', 'ha/2']
        get_cluster_nodes.return_value = ['10.0.3.2', '10.0.3.3', '10.0.3.4']
        relation_ids.return_value = ['ha:1']
        get_corosync_conf.return_value = True
        cfg = {'debug': False,
               'prefer-ipv6': False,
               'corosync_transport': 'udpu',
               'corosync_mcastaddr': 'corosync_mcastaddr',
               'cluster_count': 3,
               'maas_url': 'http://maas/MAAAS/',
               'maas_credentials': 'secret'}

        config.side_effect = lambda key: cfg.get(key)

        rel_get_data = {'locations': {'loc_foo': 'bar rule inf: meh eq 1'},
                        'clones': {'cl_foo': 'res_foo meta interleave=true'},
                        'groups': {'grp_foo': 'res_foo'},
                        'colocations': {'co_foo': 'inf: grp_foo cl_foo'},
                        'resources': {'res_foo_hostname': 'ocf:maas:dns'},
                        'resource_params': {'res_foo_hostname': 'params bar'},
                        'ms': {'ms_foo': 'res_foo meta notify=true'},
                        'orders': {'foo_after': 'inf: res_foo ms_foo'}}

        def fake_parse_data(relid, unit, key):
            return rel_get_data.get(key, {})

        parse_data.side_effect = fake_parse_data

        hooks.ha_relation_changed()
        self.assertTrue(validate_dns_ha.called)
        self.assertTrue(setup_maas_api.called)
        # Validate maas_credentials and maas_url are added to params
        commit.assert_any_call(
            'crm -w -F configure primitive res_foo_hostname ocf:maas:dns '
            'params bar maas_url="http://maas/MAAAS/" '
            'maas_credentials="secret"')

    @mock.patch.object(hooks, 'setup_maas_api')
    @mock.patch.object(hooks, 'validate_dns_ha')
    @mock.patch('pcmk.wait_for_pcmk')
    @mock.patch.object(hooks, 'peer_units')
    @mock.patch('pcmk.crm_opt_exists')
    @mock.patch.object(hooks, 'oldest_peer')
    @mock.patch.object(hooks, 'configure_corosync')
    @mock.patch.object(hooks, 'configure_cluster_global')
    @mock.patch.object(hooks, 'configure_monitor_host')
    @mock.patch.object(hooks, 'configure_stonith')
    @mock.patch.object(hooks, 'related_units')
    @mock.patch.object(hooks, 'get_cluster_nodes')
    @mock.patch.object(hooks, 'relation_set')
    @mock.patch.object(hooks, 'relation_ids')
    @mock.patch.object(hooks, 'get_corosync_conf')
    @mock.patch('pcmk.commit')
    @mock.patch.object(hooks, 'config')
    @mock.patch.object(hooks, 'parse_data')
    def test_ha_relation_changed_dns_ha_missing(
            self, parse_data, config, commit, get_corosync_conf, relation_ids,
            relation_set, get_cluster_nodes, related_units, configure_stonith,
            configure_monitor_host, configure_cluster_global,
            configure_corosync, oldest_peer, crm_opt_exists, peer_units,
            wait_for_pcmk, validate_dns_ha, setup_maas_api):

        validate_dns_ha.return_value = False
        crm_opt_exists.return_value = False
        oldest_peer.return_value = True
        related_units.return_value = ['ha/0', 'ha/1', 'ha/2']
        get_cluster_nodes.return_value = ['10.0.3.2', '10.0.3.3', '10.0.3.4']
        relation_ids.return_value = ['ha:1']
        get_corosync_conf.return_value = True
        cfg = {'debug': False,
               'prefer-ipv6': False,
               'corosync_transport': 'udpu',
               'corosync_mcastaddr': 'corosync_mcastaddr',
               'cluster_count': 3,
               'maas_url': 'http://maas/MAAAS/',
               'maas_credentials': None}

        config.side_effect = lambda key: cfg.get(key)

        rel_get_data = {'locations': {'loc_foo': 'bar rule inf: meh eq 1'},
                        'clones': {'cl_foo': 'res_foo meta interleave=true'},
                        'groups': {'grp_foo': 'res_foo'},
                        'colocations': {'co_foo': 'inf: grp_foo cl_foo'},
                        'resources': {'res_foo_hostname': 'ocf:maas:dns'},
                        'resource_params': {'res_foo_hostname': 'params bar'},
                        'ms': {'ms_foo': 'res_foo meta notify=true'},
                        'orders': {'foo_after': 'inf: res_foo ms_foo'}}

        def fake_parse_data(relid, unit, key):
            return rel_get_data.get(key, {})

        parse_data.side_effect = fake_parse_data

        with self.assertRaises(ValueError):
            hooks.ha_relation_changed()
