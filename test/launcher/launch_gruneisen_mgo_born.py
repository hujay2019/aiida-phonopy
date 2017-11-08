from aiida import load_dbenv, is_dbenv_loaded
if not is_dbenv_loaded():
    load_dbenv()

from aiida.orm import CalculationFactory, DataFactory, WorkflowFactory
from aiida.work.run import run, submit, async
from aiida.orm.data.structure import StructureData
from aiida.orm.data.base import Str, Float, Bool

#VaspCalculation = CalculationFactory('vasp.vasp')
#PwCalculation = CalculationFactory('quantumespresso.pw')
#PhonopyCalculation = CalculationFactory('phonopy')

KpointsData = DataFactory("array.kpoints")
ParameterData = DataFactory('parameter')


# Define structure

import numpy as np

cell = [[ 4.2119998932, 0,            0],
        [ 0.0,          4.2119998932, 0],
        [ 0.0,          0,           4.2119998932]]

structure = StructureData(cell=cell)

scaled_positions=[(0.0000000,  0.0000000,  0.0000000),
                  (0.0000000,  0.5000000,  0.5000000),
                  (0.5000000,  0.0000000,  0.5000000),
                  (0.5000000,  0.5000000,  0.0000000),
                  (0.5000000,  0.5000000,  0.5000000),
                  (0.5000000,  0.0000000,  0.0000000),
                  (0.0000000,  0.5000000,  0.0000000),
                  (0.0000000,  0.0000000,  0.5000000)]

symbols=['Mg', 'Mg', 'Mg' ,'Mg', 'O', 'O', 'O', 'O']

positions = np.dot(scaled_positions, cell)

for i, scaled_position in enumerate(scaled_positions):
    structure.append_atom(position=np.dot(scaled_position, cell).tolist(),
                          symbols=symbols[i])

# Machine
machine_dict = {'resources': {'num_machines': 1,
                              'parallel_env': 'mpi*',
                              'tot_num_mpiprocs': 16},
                'max_wallclock_seconds': 30 * 60,
                }


# PHONOPY settings
ph_settings = ParameterData(dict={'supercell': [[2, 0, 0],
                                                [0, 2, 0],
                                                [0, 0, 2]],
                                  'primitive': [[0.0, 0.5, 0.5],
                                                [0.5, 0.0, 0.5],
                                                [0.5, 0.5, 0.0]],
                                  'distance': 0.01,
                                  'mesh': [20, 20, 20],
                                  'symmetry_precision': 1e-5,
                                   # Uncomment the following line to use phonopy remotely
                                   # 'code': 'phonopy@boston'
                                  'machine': machine_dict
                                  })


# VASP SPECIFIC
incar_dict = {
    'NELMIN' : 5,
    'NELM'   : 100,
    'ENCUT'  : 400,
    'ALGO'   : 38,
    'ISMEAR' : 0,
    'SIGMA'  : 0.02,
    'GGA'    : 'PS'
}

es_settings = ParameterData(dict=incar_dict)

from pymatgen.io import vasp as vaspio

potcar = vaspio.Potcar(symbols=['Mg', 'O'],
                       functional='PBE')

# custom k-points
# supported_modes = Enum(("Gamma", "Monkhorst", "Automatic", "Line_mode", "Cartesian", "Reciprocal"))
kpoints_dict = {'type': 'Monkhorst',
                'points': [2, 2, 2],
                'shift': [0.0, 0.0, 0.0]}

settings_dict = {'code': {'optimize': 'vasp544mpi@boston',
                          'forces': 'vasp544mpi@boston',
                          'born_charges': 'vasp544mpi@boston'}, # Calculate and use Born effective charges
                 'parameters': incar_dict,
                 #  'kpoints': kpoints_dict,  # optional explicit definition of kpoints mesh
                 'kpoints_per_atom': 1000,  # k-point density
                 'pseudos': potcar.as_dict(),
                 'machine': machine_dict}


GruneisenPhonopy = WorkflowFactory('phonopy.gruneisen')

if True:
    result = run(GruneisenPhonopy,
                 structure=structure,
                 es_settings=es_settings,
                 ph_settings=ph_settings,
                 # Optional settings
                 # pressure=Float(0),
                 # optimize=Bool(False),
                 )

    print (result)
else:
    future = submit(GruneisenPhonopy,
                    structure=structure,
                    es_settings=es_settings,
                    ph_settings=ph_settings,
                    # Optional settings
                    # pressure=Float(0),
                    # optimize=Bool(False),
                    )

    print future
    print('Running workchain with pk={}'.format(future.pid))