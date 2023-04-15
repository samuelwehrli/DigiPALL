from tools import corsano


def corsano_load(email, password, days_ago=60):
    out = {
        'success': False,
        'status': ''
    }

    try:
        uapi, hapi, error = corsano.init_with_login(email, password)
    except:
        error = 'Login failed'

    if error:
        out['status'] = error
        return out

    # get data
    activity_data = hapi.get_data(days_ago,'activity')
    hr_data = hapi.get_data(days_ago,'heart_rate')

    if len(activity_data) == 0:
        out['status'] = f'No data within the last {days_ago} days'
        return out

    out['activity_data'] = activity_data
    out['heart_rate_data'] = hr_data
    out['min_days_ago'] = hr_data[-1]['days_ago']
    out['last_meas_date'] = hr_data[-1]['date']

    last_steps = activity_data[-1]['total_steps']
    last_hr = hr_data[-1]['avg_daily_heart_rate']
    if (last_hr < 50) or (last_hr > 150):
        if last_steps < 200:
            out['chat_opener'] = "Your pulse seemed to be low / high and you seem to have taken very few steps"
        else:
            out['chat_opener'] = "Your pulse seemed to be low / high"
    else:
        if last_steps < 200:
            out['chat_opener'] = "You seem to have taken very few steps"
        else:
            out['chat_opener'] = "Your biomarkers are all within a normal range"

    out['status'] = f'Last measurement was {out["min_days_ago"]} day(s) ago on {out["last_meas_date"]}'+\
                    f' with {last_steps} steps and an average heart rate of {last_hr} bpm.'
    out['success'] = True


    return out

