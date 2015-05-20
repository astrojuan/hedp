#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright CNRS 2012
# Roman Yurchak (LULI)
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software.

import numpy as np
from ..matdb import matdb
from .definitions import find_files



class FlashEosMaterials(dict):
    def __init__(self, header, p, eos_dirs=['./', ], op_dirs=['./'], Zmin=0.1, temp0=None):
        """
        Convinience class to setup the EoS and opacities of a FLASH simulation
        """
        self.header = header
        self.p = p
        self.Zmin = Zmin
        self.eos_dirs = eos_dirs
        self.op_dirs = op_dirs 
        self.temp0=temp0

        self.materials = [key.split('_')[0].lower() for key in header \
                                if key.endswith('_SPEC')]
        self.num_materials = len(self.materials)
        self.data = {key: {} for key in self.materials}

    def set(self, spec, matid, eos_table=None, op_table=None, **args):
        """
        Set a FLASH material
         
        Parameters
        ----------
          - spec: flash species id
          - matid: material id from hedp.matdb
        """
        if spec not in self.materials:
            raise KeyError

        mat = matdb(matid)
 

        self.data[spec]['material'] = matid

        for key in ['A', 'Z', 'Zmin']:
            if key in args:
                val = args[key]
            elif key == 'Zmin':
                val = self.Zmin
            else:
                val = mat[key]
            self['ms_{0}{1}'.format(spec, key)] = val
            self.data[spec][key] = val

        for key in ['rho', 'tele', 'trad', 'tion']:
            if key in args:
                val = args[key]
            elif key == 'rho':
                val = mat['rho0']
            elif self.temp0 is not None:
                val = self.temp0
            else: # this is a temperature and we set it to 300K (i.e. room temperature)
                val = 300.

            self['sim_{}{}'.format(key, spec)] = val
            self.data[spec][key] = val

        if matid == 'vacuum':
            vacuum_pars = { "ms_{}gamma": 1.15,
                            "eos_{}EosType": "eos_gam",
                            "op_{}Absorb" : "op_constant",
                            "op_{}Emiss" : "op_constant",
                            "op_{}Trans" : "op_constant",
                            "op_{}AbsorbConstant" : 1e-5,
                            "op_{}EmissConstant" : 1e-5,
                            "op_{}TransConstant" : 1e-5,
                            }
            self.update({key.format(spec): val for key, val in vacuum_pars.items()})
            self.data[spec]['eos_table'] = matid
            self.data[spec]['op_table'] = matid
        else:
            if eos_table is None:
                raise ValueError
            if op_table is None:
                raise ValueError
            vacuum_pars = { "op_{}Absorb" : "op_tabpa",
                            "op_{}Emiss" : "op_tabpe",
                            "op_{}Trans" :  "op_tabro",
                            "op_{}FileType" : "ionmix4",
                            "eos_{}EosType" : "eos_tab",
                            "eos_{}SubType" : "ionmix4",
                            }
            self.update({key.format(spec): val for key, val in vacuum_pars.items()})

            matches = find_files(self.eos_dirs, eos_table)
            if not matches:
                raise ValueError('Could not find any matching EoS file {} in \n {}'.format(eos_table, self.eos_dirs))
            if len(matches)>1:
                print('Warning: found multiple EoS files for {},\n {}'.format(eos_table, matches))
                print('         taking the first table!')


            self.data[spec]['eos_table'] = matches[0]

    def validate(self):
        value = ~np.asarray([not self.data[spec] for spec in self.materials])
        if value.all():
            return True
        else:
            idx = np.nonzero(value)[0]
            print(idx)
            raise ValueError('Species {} has not been initialized!'.format( np.asarray(self.materials)[idx]))

    def __repr__(self):
        """
        Pretty print the laser parameters
        """

        self.validate()

        labels  = ['material',
                   'A',
                   'Z',
                   'Zmin',
                   'rho',
                   'tele',
                   'tion',
                   'trad',
                   ]

        entry_format = ['{:>10}',
                        '{:>10}',
                        '{:>10}',
                        '{:>10}',
                        '{:>10.3e}',
                        '{:>10.3e}',
                        '{:>10.3f}',
                        '{:>10.3f}',
                        ]


        out = ['', '='*80, ' '*26 + 'Material parameters', '='*80]

        row_format_labels ="{:10}" + "{:>10}" * self.num_materials

        out.append(row_format_labels.format('', *self.materials))

        for key, fmt in zip(labels, entry_format):
            row_format ="{:18}" + fmt*self.num_materials
            values = [self.data[spec][key] for spec in self.materials]
            out.append(row_format.format(label, *values))


        out += ['='*80, '']

        return '\n'.join(out)






