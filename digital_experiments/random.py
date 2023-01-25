from datetime import datetime

import numpy as np

repeatable_random = np.random.RandomState(seed=1)
truly_random = np.random.RandomState(seed=datetime.now().microsecond)
