import pandas as pd
import numpy as np

from lib.etypes import ETYPE, read_raw_dataset, append_to_tmp_dataset, exctract_and_fetch_positions, read_tmp_dataset, write_tmp_dataset
from lib.utils import check_duplicates, err, warn, info, add_id_prefix, positions_near_enough

users = read_raw_dataset(ETYPE.USER)
users = add_id_prefix(users, 'user_')

# Read tmp positions dataset
positions = read_tmp_dataset(ETYPE.POSITION)
if positions is not None:
  user_positions = positions.loc[positions['id'].astype(str).str.contains('pos_user_dom_|pos_user_res_')]

# Fetch positions if needed
if user_positions is None or len(user_positions) <= len(users):
  print('Fetching positions...') 
  user_positions = pd.concat([
    exctract_and_fetch_positions(users, 'domicile_location', 'pos_user_dom_'),
    exctract_and_fetch_positions(users, 'residence_location', 'pos_user_res_'),
  ])
  append_to_tmp_dataset(ETYPE.POSITION, user_positions, False)
  positions = read_tmp_dataset(ETYPE.POSITION)

# Remove duplicates (FIXME change duplciates id prefix?)
# positions.drop_duplicates(subset='address', inplace=True)
# check_duplicates(positions, ['address'])

# Link positions to users
pos_address_id_map = dict(zip(positions['address'], positions['id']))
users['domiciled'] = users['domicile_location'].map(pos_address_id_map)
users['reside'] = users['residence_location'].map(pos_address_id_map)

stops_position = positions.loc[positions['id'].str.contains('pos_stop')]
if stops_position is not None and len(stops_position) > 0:
  stops_position.set_index('id', inplace=True)
  positions.set_index('id', inplace=True)

  def find_nearest_stops(pos):
    pos = positions.loc[pos]
    near_stops = stops_position.loc[stops_position.apply(lambda s: positions_near_enough(pos, s), axis=1)]
    return '|'.join(near_stops.index) if len(near_stops) > 0 else ""

  for c in ['domiciled', 'reside']:
    users['nearest_stops_' + c] = users[c].apply(find_nearest_stops)

  positions.reset_index(inplace=True)
else:
  err('Could not link from/to locations, please generate educational facilities and stops tmp dataset!')

# Read tmp positions dataset
positions = read_tmp_dataset(ETYPE.POSITION)
pos_address_id_map = dict(zip(positions['address'], positions['id']))

if positions is not None and len(positions) > 0:
  users['work'] = users['work_location'].map(pos_address_id_map)
else:
  users['work'] = None
  err('Could not link work locations, please generate educational facilities tmp dataset!')

# Schedules
shifts = read_raw_dataset(ETYPE.SHIFT)
schedules = read_raw_dataset(ETYPE.WEEKLY_SCHEDULE, custom_path='users/calendar')
schedules_exceptions = read_raw_dataset(ETYPE.SCHEDULE_EXCEPTION, custom_path='users/calendar_dates')
for c in ['from', 'to']:
  shifts[c] = shifts[c].map(pos_address_id_map)


users = write_tmp_dataset(ETYPE.USER, users)
shifts = write_tmp_dataset(ETYPE.SHIFT, shifts)
# positions = append_to_tmp_dataset(ETYPE.POSITION, positions, False)
schedules = append_to_tmp_dataset(ETYPE.WEEKLY_SCHEDULE, schedules, False)
schedules_exceptions = append_to_tmp_dataset(ETYPE.SCHEDULE_EXCEPTION, schedules_exceptions, False)

print(
  '\n\nUSERS\n', users,
  '\n\nPOSITIONS\n', positions,
  '\n\nWEEKLY SCHEDULE\n', schedules,
  '\n\nSCHEDULE EXCEPTION\n', schedules_exceptions,
  '\n\nSHIFTS\n', shifts
)

