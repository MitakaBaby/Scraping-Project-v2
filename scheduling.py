from common import Utils, DataFrames


data_frames = DataFrames()

def sites_to_run():

    day_mapping = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    site_lists = {
        "sites_at_01_30": {
            "Monday": [
                
                
                ],
            "Tuesday": [
                
                
                ],
            "Wednesday": [
                
                
                ],
            "Thursday": [
                
                
                ],
            "Friday": [
                
                
                ],
            "Saturday": [
                
                
                ],
            "Sunday": [
                
                
                ],
            "Daily": [

                ]
        },       
        "sites_at_02_00": {
            "Monday": [
                
                
                ],
            "Tuesday": [
                
                
                ],
            "Wednesday": [
                
                
                ],
            "Thursday": [
                
                
                ],
            "Friday": [
                
                
                ],
            "Saturday": [
                
                
                ],
            "Sunday": [
                
                
                ],
            "Daily": [

                ]
        },
        "sites_at_03_00": {
            "Monday": [
                
                
                ],
            "Tuesday": [

                ],
            "Wednesday": [
                
                ],
            "Thursday": [
                
                
                ],
            "Friday": [
                
                
                ],
            "Saturday": [
                
                
                ],
            "Sunday": [
                
                
                ],
            "Daily": [

                ]
        },
        "sites_at_06_00": {
            "Monday": [
                

                ],
            "Tuesday": [


                ],
            "Wednesday": [
                

                ],
            "Thursday": [
                

                ],
            "Friday": [
                

                ],
            "Saturday": [
                

                ],
            "Sunday": [
                

                ],
            "Daily": [

                ]
        },
        "sites_at_07_00": {
            "Monday": [
                
                ],
            "Tuesday": [
                
                ],
            "Wednesday": [
                
                ],
            "Thursday": [
                
                ],
            "Friday": [
                
                ],
            "Saturday": [
                
                ],
            "Sunday": [
                
                ],
            "Daily": [

                ]
        },
        "sites_at_07_30": {
            "Monday": [
                
                ],
            "Tuesday": [
                
                ],
            "Wednesday": [

                ],
            "Thursday": [
                
                ],
            "Friday": [
                
                ],
            "Saturday": [
                
                ],
            "Sunday": [
                
                ],
            "Daily": [
                
                ]
        },        
        "sites_at_08_00": {
            "Monday": [

                ],
            "Tuesday": [

                ],
            "Wednesday": [

                ],
            "Thursday": [

                ],
            "Friday": [

                ],
            "Saturday": [

                ],
            "Sunday": [

                ],
            "Daily": [

                ]
        },
        "sites_at_09_00": {
            "Monday": [
                
                ],
            "Tuesday": [
                
                ],
            "Wednesday": [

                ],
            "Thursday": [
                
                ],
            "Friday": [
                
                ],
            "Saturday": [

                ],
            "Sunday": [
                
                ],
            "Daily": [

                ]
        },   
        "sites_at_10_00": {
            "Monday": [

                ],
            "Tuesday": [

                ],
            "Wednesday": [

            "Thursday": [

                ],
            "Friday": [

                ],
            "Saturday": [

                ],
            "Sunday": [

                ],
            "Daily": [

                ]
        },
        "sites_at_12_00": {
            "Monday": [
                
                ],
            "Tuesday": [
                
                ],
            "Wednesday": [
                
                ],
            "Thursday": [
                
                ],
            "Friday": [
              
                ],
            "Saturday": [
                
                ],
            "Sunday": [
                
                ],
            "Daily": [

                ]
        },
        "sites_at_17_00": {
            "Monday": [
                
                ],
            "Tuesday": [
                
                ],
            "Wednesday": [
                
                ],
            "Thursday": [
                
                ],
            "Friday": [
                
                ],
            "Saturday": [
            
                ],
            "Sunday": [
                
                ],
            "Daily": [

                ]
        },
        "sites_at_19_00": {
            "Monday": [
                

                ],
            "Tuesday": [

                ],
            "Wednesday": [
                
                ],
            "Thursday": [

                ],
            "Friday": [

                ],
            "Saturday": [
                
                
                ],
            "Sunday": [
                
                
                ],
            "Daily": [

                ]
        },
        "sites_at_20_30": {
            "Monday": [

                ],
            "Tuesday": [

                ],
            "Wednesday": [

                ],
            "Thursday": [

                ],
            "Friday": [

                ],
            "Saturday": [

                ],
            "Sunday": [

                ],
            "Daily": [

                ]
        },    
        "sites_at_21_00": {
            "Monday": [
                ],
            "Tuesday": [

                ],
            "Wednesday": [
                
                ],
            "Thursday": [
                
                ],
            "Friday": [
                
                ],
            "Saturday": [
              
                ],
            "Sunday": [
                
                ],
            "Daily": [

                ]
        },    
        "sites_at_23_00": {
            "Monday": [
                
                ],
            "Tuesday": [
                
                ],
            "Wednesday": [
                
                ],
            "Thursday": [
                
                ],
            "Friday": [
                
                ],
            "Saturday": [
                
                ],
            "Sunday": [
                
                ],
            "Daily": [

                ]
        },
        "not_sorted":{
            "Monday": [

                ],
            "Tuesday": [

                ],
            "Wednesday": [

                ],
            "Thursday": [

                ],
            "Friday": [


                ],
            "Saturday": [


                ],
            "Sunday": [


                ],
            "Daily": [
              
                ]
        }
    }

    sites_to_run = []

    for list_name, day_list in site_lists.items():
        current_day = day_mapping.get(Utils.get_day_of_week())
        current_time = Utils.get_current_time()
        value = data_frames.read_save_schedule_df(list_name)
        if value == "Yes":
            continue
        elif value == "No":
            if current_day in day_list:
                sites_list_for_current_day = day_list[current_day]
                daily_sites = day_list.get("Daily", [])
                if current_time > "01:30:00" and "sites_at_01_30" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "02:15:00" and "sites_at_02_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "03:15:00" and "sites_at_03_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "06:15:00" and "sites_at_06_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "07:15:00" and "sites_at_07_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "07:45:00" and "sites_at_07_30" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "08:15:00" and "sites_at_08_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "09:15:00" and "sites_at_09_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "10:15:00" and "sites_at_10_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "12:15:00" and "sites_at_12_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "17:15:00" and "sites_at_17_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "19:15:00" and "sites_at_19_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "20:35:00" and "sites_at_20_30" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "21:00:00" and "sites_at_21_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif current_time > "23:00:00" and "sites_at_23_00" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
                    data_frames.update_schedule_df(list_name)
                elif "not_sorted" in list_name:
                    if daily_sites:
                        sites_to_run.append(daily_sites)
                    if sites_list_for_current_day:
                        sites_to_run.append(sites_list_for_current_day)
        else:
            print(f"Problem with {list_name}.")
    sites_to_run = [site for sublist in sites_to_run for site in sublist]

    return sites_to_run
