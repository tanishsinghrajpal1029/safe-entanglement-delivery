import os, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(os.path.dirname(HERE))
DATA=os.path.join(ROOT,'data/Data/Full_tomography')
CACHE=os.path.join(HERE,'cache')
# run map from Full_tomography/Basis_timestamps.png (Basis NodeA-NodeB, NodeA folder, NodeB folder, photon file)
RUNS=[('1819','182128','2021_07_20_182031','Z','Z'),
      ('1856','185817','2021_07_20_185539','Z','X'),
      ('1920','192216','2021_07_20_191636','Z','Y'),
      ('2143','214507','2021_07_20_214405','X','Z'),
      ('2243','224512','2021_07_20_224420','X','X'),
      ('0014','001652','2021_07_21_001507','X','Y'),
      ('2203','220456','2021_07_20_220327','Y','Z'),
      ('2349','235147','2021_07_20_235032','Y','X'),
      ('2302','230420','2021_07_20_230331','Y','Y')]
def load_tags(b):
    return np.load(f'{CACHE}/{b}_t.npy'), np.load(f'{CACHE}/{b}_c.npy')
