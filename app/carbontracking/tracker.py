from flask import Flask, render_template, request, jsonify
#import geocoder
import statistics
from collections import Counter
import time
import threading
import json
from functools import reduce
from .db_app import db, app, train_devices, inference_devices, hostgpus, Task, Model, Hostgpu, Trackinginfo, Inferenceinfo, Powermix


    
### DATABASE FUNCTIONS ###
def add_init_entry(mode, model, task, hardware, host):
    """
    Adds an initial entry to the database for a given mode, model, task, hardware, and host.

    Parameters:
    - mode (str): The mode of the entry (e.g., "inference").
    - model (str): The name of the model.
    - task (str): The name of the task.
    - hardware (list): A list of hardware devices.
    - host (str): The name of the host.

    Returns:
    - updated_task_name (str): The updated task name.
    - dev_ids (dict): A dictionary mapping hardware devices to their corresponding IDs.
    """
    updated_task_name = ""
    existing_model = Model.query.filter_by(model_name=model, task=task).first()
    if not existing_model:
        updated_task_name = task
    else:
        i = 1
        while True:
            updated_task_name = f"{task}_{i}"
            existing_model = Model.query.filter_by(model_name=model, task=updated_task_name).first()
            if not existing_model:
                break
            i += 1

    inference_info = Inferenceinfo.query.filter_by(task_name_inf=task, model_inf=model).first()  
    if updated_task_name != task and mode == "inference" and not inference_info:
        updated_task_name = task
    
    elif inference_info and mode == "inference":
        i = 1
        while True:
            updated_task_name = f"{task}_{i}"
            inference_info = Inferenceinfo.query.filter_by(task_name_inf=updated_task_name, model_inf=model).first()
            if not inference_info:
                break
            i += 1

    existing_model = Model.query.filter_by(model_name=model, task=updated_task_name).first()
    existing_task = Task.query.filter_by(task=updated_task_name).first()

    if not existing_model:
        new_model = Model(model_name=model, task=updated_task_name)
        db.session.add(new_model)
        db.session.commit()

    if not existing_task:
        new_task = Task(task=updated_task_name)
        db.session.add(new_task)
        db.session.commit()

    dev_ids = {}
    for dev in hardware:
        if "gpu" in dev.lower() or "cpu" in dev.lower():
            host_exists = Hostgpu.query.filter_by(host=host, gpu_cpu=dev).first()
            if host_exists is None:
                new_host_gpu = Hostgpu(
                host=host,
                gpu_cpu=dev
            )
                db.session.add(new_host_gpu)
                db.session.commit()

            query = db.session.query(Hostgpu.id).filter(Hostgpu.host == host, Hostgpu.gpu_cpu == dev).first()
            if host_exists and existing_task:
                dev_ids[dev] = query[0]
            else:
                if query:
                    dev_ids[dev] = query[0]
                else:
                    dev_ids[dev] = new_host_gpu.id

                # Associate the task with the host GPU
                if existing_task and query:
                    new_hostgpus = hostgpus.insert().values(task_id=updated_task_name, hostgpu_host=query[0])
                elif not existing_task and not query:
                    new_hostgpus = hostgpus.insert().values(task_id=new_task.task, hostgpu_host=new_host_gpu.id)
                elif not existing_task and query:
                    new_hostgpus = hostgpus.insert().values(task_id=new_task.task, hostgpu_host=query[0])

                db.session.execute(new_hostgpus)
                db.session.commit()

    return updated_task_name, dev_ids

def add_train_entry(timestamp, carb_int=None, power_usg=None, CO2_usg=None, task=None, 
                model=None, elapsed_time=None, dev_ids=None, hardware_distr=None, start=None):
    """
    Add a train entry to the database.

    Args:
        timestamp (datetime): The timestamp of the train entry.
        carb_int (float, optional): The carbon intensity. Defaults to None.
        power_usg (float, optional): The power usage. Defaults to None.
        CO2_usg (float, optional): The CO2 usage. Defaults to None.
        task (str, optional): The task name. Defaults to None.
        model (str, optional): The model name. Defaults to None.
        elapsed_time (float, optional): The elapsed time. Defaults to None.
        dev_ids (dict, optional): The dictionary of device IDs. Defaults to None.
        hardware_distr (dict, optional): The dictionary of hardware distribution. Defaults to None.
        start (bool, optional): Indicates if it's the start of a train. Defaults to None.
    """
    # Create a data entry and add it to the database
    new_entry = Trackinginfo(
        timestamp=timestamp,
        carbon_intensity=carb_int,
        power_usage=power_usg,
        CO2_usage=CO2_usg,
        task_name=task,
        model=model,
        elapsed_time=elapsed_time,
        task_model=f"{task}_{model}"
    )
    db.session.add(new_entry)
    db.session.commit()
    
    for dev, dev_id in dev_ids.items():  
        new_hostdevice = train_devices.insert().values(tracking_info_id=new_entry.id, hostgpu_id=dev_id, CO2_usage=hardware_distr[dev]*carb_int, power_usg=hardware_distr[dev])
        db.session.execute(new_hostdevice)
        db.session.commit()

def add_inference_entry(timestamp, carb_int=None, power_usg=None, CO2_usg=None, task=None,
              model=None, elapsed_time=None, dev_ids=None, hardware_distr=None):
    """
    Add a train entry to the database.

    Args:
        timestamp (datetime): The timestamp of the train entry.
        carb_int (float, optional): The carbon intensity. Defaults to None.
        power_usg (float, optional): The power usage. Defaults to None.
        CO2_usg (float, optional): The CO2 usage. Defaults to None.
        task (str, optional): The task name. Defaults to None.
        model (str, optional): The model name. Defaults to None.
        elapsed_time (float, optional): The elapsed time. Defaults to None.
        dev_ids (dict, optional): The dictionary of device IDs. Defaults to None.
        hardware_distr (dict, optional): The dictionary of hardware distribution. Defaults to None.
        start (bool, optional): Indicates if it's the start of a train. Defaults to None.
    """

    # Create a data entry and add it to the database
    new_entry = Inferenceinfo(
        timestamp_inf=timestamp,
        carbon_intensity_inf=carb_int,
        power_usage_inf=power_usg,
        CO2_usage_inf=CO2_usg,
        task_name_inf=task,
        model_inf=model,
        elapsed_time_inf=elapsed_time,
        task_model_inf=f"{task}_{model}"
    )
    db.session.add(new_entry)
    db.session.commit()

    for dev, dev_id in dev_ids.items():
        new_hostdevice = inference_devices.insert().values(inference_info_id=new_entry.id, hostgpu_id=dev_id, CO2_usage=hardware_distr[dev])
        db.session.execute(new_hostdevice)
        db.session.commit()

def get_power_mix():
    """
    Retrieves the power mix.

    Returns:
    - power_mix (dict): The power mix.
    """
    power_mix = Powermix.query.order_by(Powermix.timestamp.desc()).first()
    power_mix = power_mix.powermix.replace("\'", "\"")
    return json.loads(power_mix)

### HELPER FUNCTIONS ###
def get_initial_data():
    tracking_info_entries = Trackinginfo.query.all()
    task_entries = Task.query.all()
    hostgpu_entries = Hostgpu.query.all()
    model_entries = Model.query.all()   
    #hostgpus_entries = db.session.query(hostgpus)

    return tracking_info_entries, task_entries, hostgpu_entries, model_entries

def get_carbon_data(update_data):
    """
    Retrieves carbon data based on the provided update data.

    Args:
        update_data (dict): The update data containing information about tasks, GPUs, hosts, and models.

    Returns:
        tuple: A tuple containing the following carbon data:
            - tracking_info (dict): A dictionary containing tracking information for each task.
            - carb_int_average (float): The average carbon intensity.
            - power_usg_sum (float): The sum of power usage.
            - CO2_usg_sum (float): The sum of CO2 usage.
            - elapsed_time (dict): A dictionary containing elapsed time for each task.
            - train_info (dict): A dictionary containing training information for each task.
    """
    tracking_info = {}
    carb_int = []
    power_usg = []
    CO2_usg = []
    elapsed_time = {}

    for task in update_data['tasks']:
        curr_tracking_info = db.session.execute(db.select(train_devices.c.CO2_usage, train_devices.c.power_usg, Trackinginfo.carbon_intensity,
                                                          Trackinginfo.model, Trackinginfo.elapsed_time,Trackinginfo.task_model, 
                                                          Hostgpu.gpu_cpu, Hostgpu.host, train_devices.c.tracking_info_id) \
                                                         .join(train_devices, Trackinginfo.id == train_devices.c.tracking_info_id)\
                                                         .join(Hostgpu, Hostgpu.id == train_devices.c.hostgpu_id) \
                .filter(Trackinginfo.task_name == task) \
                .filter(Hostgpu.gpu_cpu.in_(update_data["gpus"]))\
                .filter(Hostgpu.host.in_(update_data["hosts"]))\
                .filter(Trackinginfo.task_model.in_(update_data["models"]))\
                ).fetchall()

        tracking_info[task] = curr_tracking_info

    train_info = {key: [(entry[0], entry[7], entry[6]) for entry in value] for key, value in tracking_info.items()}
    aggregated_data = {}

    for key, values in tracking_info.items():
        visited = set()
        aggregated_data[key] = []
        for value in values:
            group_key = value[-1]  
            len_entry = len(values) / len(values[values[-1]==group_key])
            if group_key not in visited:
                    aggregated_data[key].append([
                        value[0], value[1], value[2], value[3], value[4], value[5], value[6]
                    ])
                    visited.add(group_key)
            else:
                aggregated_data[key][-1][:2] = [sum(val) for val in zip(aggregated_data[key][-1][:2], value[:2])]
                aggregated_data[key][-1][2] = value[2]
                aggregated_data[key][-1][3] = value[3]
                aggregated_data[key][-1][4] += value[4]
                aggregated_data[key][-1][5:7] = value[5:7]

        aggregated_data = {key: [[val[i] / len_entry if i == 4 else val[i] 
                                  for i in range(len(val))] for val in values] for key, values in aggregated_data.items()}

    for key, value in aggregated_data.items():
        elapsed_time[key] = [(val[4], val[3]) for val in value]
        tracking_info[key] = [(val[0], val[3], val[5]) for val in value]
        carb_int.append([val[2] for val in value])
        power_usg.append([val[1] for val in value])
        CO2_usg.append([val[0] for val in value])
    
    # Calculate the aggregations of key values
    CO2_usg = reduce(lambda x,y: x+y, CO2_usg)
    power_usg = reduce(lambda x,y: x+y, power_usg)
    carb_int = reduce(lambda x,y: x+y, carb_int)

    print(carb_int)
    try:
        carb_int_average = statistics.mean(carb_int)
    except statistics.StatisticsError:
        carb_int_average=0
        print("No train data yet, skipping, ....")


    try:
        sum_co2 = CO2_usg[-1]
    except IndexError:
        return tracking_info, carb_int_average, 0, 0, elapsed_time, train_info

    sum_power = power_usg[-1]  
    for i in range(len(CO2_usg)):
        if i==0:
            last = CO2_usg[i] 
            last_p = power_usg[i]
            continue
        else:
            if CO2_usg[i] < last:
                sum_co2 += last
                sum_power += last_p
        last = CO2_usg[i]
        last_p = power_usg[i]

    return tracking_info, carb_int_average, sum_power, sum_co2, elapsed_time, train_info

def get_inf_data(update_data):
    """
    Retrieves inference information based on the provided update_data.

    Args:
        update_data (dict): A dictionary containing the update data.

    Returns:
        tuple: A tuple containing three elements:
            - inference_info_averages (list): A list of tuples containing the average CO2 usage for every unique task and model combination.
            - elapsed_time_inf (dict): A dictionary containing the elapsed time for each task.
            - inference_info (dict): A dictionary containing the inference information for each task.

    """
    inference_info = {}
    elapsed_time_inf = {}

    for task in update_data['tasks']:
        curr_inf_info = db.session.execute(db.select(inference_devices.c.CO2_usage, Inferenceinfo.carbon_intensity_inf, Inferenceinfo.power_usage_inf, Inferenceinfo.model_inf, 
                                                     Inferenceinfo.elapsed_time_inf, Inferenceinfo.task_model_inf, Hostgpu.gpu_cpu)\
                                                    .join(inference_devices, Inferenceinfo.id == inference_devices.c.inference_info_id)\
                                                    .join(Hostgpu, Hostgpu.id == inference_devices.c.hostgpu_id) \
            .filter(Inferenceinfo.task_name_inf == task) \
            .filter(Hostgpu.gpu_cpu.in_(update_data["gpus"]))\
            .filter(Hostgpu.host.in_(update_data["hosts"]))\
            .filter(Inferenceinfo.task_model_inf.in_(update_data["models"]))\
            ).fetchall()
        inference_info[task] = curr_inf_info

    # Calculate the average CO2_usage for every unique task and model combination
    inference_info_averages = []
    for task, info in inference_info.items():
        model_co2_usage = {}
        for entry in info:
            model = entry[3]
            co2_usage = entry[0]
            if model not in model_co2_usage:
                model_co2_usage[model] = [co2_usage]
            else:
                model_co2_usage[model].append(co2_usage)
        for model, co2_usage_list in model_co2_usage.items():
            average_co2_usage = sum(co2_usage_list) / len(co2_usage_list)
            inference_info_averages.append((task, model, average_co2_usage))

    inference_info = {key: [(entry[0], entry[-1]) for entry in value] for key, value in inference_info.items()}

    return inference_info_averages, elapsed_time_inf, inference_info
    
def get_carbon_intensity(time_dur=None):
    """api_keys = {"electricitymaps": "ESfskPIAkjDJQSPVbKdwJzR1tDM7DHko"}
    elec_map = elect_map.ElectricityMap()      
    elec_map.set_api_key(api_keys["electricitymaps"])  
    carbon_intensity = None
    g_location = geocoder.ip("me")
    carbon_intensity, power_mix = elec_map.carbon_intensity(g_location, time_dur)
    carbon_intensity.address = g_location.address
    ci = carbon_intensity.carbon_intensity
    address = carbon_intensity.address
    return ci, address, power_mix"""

    from entsoe import EntsoePandasClient
    import pandas as pd

    client = EntsoePandasClient(api_key="6d6f58a3-1d96-4ea4-a12d-5816d5e81d6f")

    start = pd.Timestamp.now(tz='Europe/Brussels') - pd.Timedelta(hours=3)
    end = pd.Timestamp.now(tz='Europe/Brussels')

    country_code = 'DE'  # Deutschland

    loads = client.query_generation(country_code, start=start, end=end)

    cis = {"Biomass": 230, "Fossil Brown coal/Lignite": 1167, "Fossil Gas":572, "Fossil Hard coal":1167, "Fossil Oil":1170, 
           "Geothermal":38, "Hydro Pumped Storage":419, "Hydro Run-of-river and poundage":11, "Hydro Water Reservoir":11,  
            "Other":700, "Other renewable":50, "Solar":35, "Waste": 580, "Wind Offshore": 13, "Wind Onshore": 13}

    carbon_intensity = 0 
    sum_emissions = 0   
    
    power_mix = {}
    for time, row in loads[::-1].iterrows():
        if not row.isnull().values.any():
            for index, value in row.items():
                if str(index[0]) in str(list(power_mix.keys())):
                    power_mix[index[0]] += value
                else:
                    power_mix[index[0]] = value

                sum_emissions += value
                carbon_intensity += cis[index[0]] * value
            break
    
    carbon_intensity = carbon_intensity / sum_emissions
    print(carbon_intensity)
    
    return carbon_intensity/1000, "address", power_mix


### FUNCTIONS TO GET DYNAMIC CHART DATA FOR DASHBOARD ###
def get_chart_data(data, largest_task_length):
    chart_data = {
        "type": "line",
        "data": {
            "labels": [],
            "datasets": []
        },
        "options": {
            "maintainAspectRatio": False,
            "legend": {
                "display": True, 
                "labels": {
                    "fontStyle": "normal"
                }
            },
            "title": {
                "fontStyle": "normal"
            },
            "scales": {
                "xAxes": [
                    {
                        "gridLines": {
                            "color": "rgb(234, 236, 244)",
                            "zeroLineColor": "rgb(234, 236, 244)",
                            "drawBorder": False,
                            "drawTicks": False,
                            "borderDash": ["2"],
                            "zeroLineBorderDash": ["2"],
                            "drawOnChartArea": False
                        },
                        "ticks": {
                            "fontColor": "#858796",
                            "fontStyle": "normal",
                            "padding": 20
                        }
                    }
                ],
                "yAxes": [
                    {
                        "gridLines": {
                            "color": "rgb(234, 236, 244)",
                            "zeroLineColor": "rgb(234, 236, 244)",
                            "drawBorder": False,
                            "drawTicks": False,
                            "borderDash": ["2"],
                            "zeroLineBorderDash": ["2"]
                        },
                        "ticks": {
                            "fontColor": "#858796",
                            "fontStyle": "normal",
                            "padding": 20
                        }
                    }
                ]
            }
        }
    }

    colors = [
        "rgba(78, 115, 223, 0.05)",
        "rgba(223, 78, 115, 0.05)",
        "rgba(115, 223, 78, 0.05)",
        "rgba(223, 115, 78, 0.05)",
        "rgba(78, 223, 115, 0.05)",
        "rgba(115, 78, 223, 0.05)",
        "rgba(223, 223, 78, 0.05)",
        "rgba(78, 223, 223, 0.05)",
        "rgba(223, 78, 223, 0.05)",
        "rgba(115, 115, 223, 0.05)",
        "rgba(223, 115, 115, 0.05)",
        "rgba(115, 223, 223, 0.05)",
        "rgba(223, 223, 115, 0.05)",
        "rgba(78, 115, 78, 0.05)",
        "rgba(115, 78, 78, 0.05)",
        "rgba(223, 78, 223, 0.05)",
        "rgba(78, 223, 78, 0.05)",
        "rgba(223, 115, 223, 0.05)",
        "rgba(115, 223, 115, 0.05)",
        "rgba(223, 223, 223, 0.05)"
    ]

    datasets = {}         
    for key in data.keys():
        for i in range(len(data[key])):
            curr_model = data[key][i][1]
            label = key + "_" + data[key][i][1]
            
            # Add all values to the dictionary at entry curr_model
            values = [value[0] for value in data[key] if value[1] == curr_model]
            datasets[label] = values

    for i, (label, dataset) in enumerate(datasets.items()):
        chart_data["data"]["datasets"].append({
            "label": label,
            "fill": True,
            "data": dataset,
            "backgroundColor": colors[i % len(colors)],
            "borderColor": colors[i % len(colors)].replace("0.05", "1"),
            "borderWidth": 3,
        })

    chart_data["data"]["labels"] = [i for i in range(1, largest_task_length + 1)]

    return chart_data

def get_chart_data_inf(inf_data):
    chart_data_inf = {
        "type": "bar",
        "data": {
            "labels": [],
            "datasets": []
        },
        "options": {
            "maintainAspectRatio": False,
            "legend": {
                "display": True, 
                "labels": {
                    "fontStyle": "normal"
                }
            },
            "title": {
                "fontStyle": "normal"
            },
            "scales": {
                "xAxes": [
                    {
                        "gridLines": {
                            "color": "rgb(234, 236, 244)",
                            "zeroLineColor": "rgb(234, 236, 244)",
                            "drawBorder": False,
                            "drawTicks": False,
                            "borderDash": ["2"],
                            "zeroLineBorderDash": ["2"],
                            "drawOnChartArea": False
                        },
                        "ticks": {
                            "fontColor": "#858796",
                            "fontStyle": "normal",
                            "padding": 20
                        }
                    }
                ],
                "yAxes": [
                    {
                        "gridLines": {
                            "color": "rgb(234, 236, 244)",
                            "zeroLineColor": "rgb(234, 236, 244)",
                            "drawBorder": False,
                            "drawTicks": False,
                            "borderDash": ["2"],
                            "zeroLineBorderDash": ["2"]
                        },
                        "ticks": {
                            "fontColor": "#858796",
                            "fontStyle": "normal",
                            "padding": 20,
                            "beginAtZero": True 
                        }
                    }
                ]
            }
        }
    }

    colors = [
        "rgba(78, 115, 223, 0.05)",
        "rgba(223, 78, 115, 0.05)",
        "rgba(115, 223, 78, 0.05)",
        "rgba(223, 115, 78, 0.05)",
        "rgba(78, 223, 115, 0.05)",
        "rgba(115, 78, 223, 0.05)",
        "rgba(223, 223, 78, 0.05)",
        "rgba(78, 223, 223, 0.05)",
        "rgba(223, 78, 223, 0.05)",
        "rgba(115, 115, 223, 0.05)",
        "rgba(223, 115, 115, 0.05)",
        "rgba(115, 223, 223, 0.05)",
        "rgba(223, 223, 115, 0.05)",
        "rgba(78, 115, 78, 0.05)",
        "rgba(115, 78, 78, 0.05)",
        "rgba(223, 78, 223, 0.05)",
        "rgba(78, 223, 78, 0.05)",
        "rgba(223, 115, 223, 0.05)",
        "rgba(115, 223, 115, 0.05)",
        "rgba(223, 223, 223, 0.05)"
    ]

    for i, elem in enumerate(inf_data):
        task, model, data = elem
        chart_data_inf["data"]["datasets"].append({
            "label": task + "_" + model,
            "fill": True,
            "data": [data],
            "backgroundColor": colors[i % len(colors)],
            "borderColor": colors[i % len(colors)].replace("0.05", "1"),
            "borderWidth": 3
        })


    return chart_data_inf

def get_chart_data_power_mix(power_mix):
    chart_data_power_mix = {
        "type": "doughnut",
        "data": {
            "labels": list(power_mix.keys()),
            "datasets": [
                {
                    "data": list(power_mix.values()),
                    "backgroundColor": ["darkgreen", "darkblue", "yellow", "lightblue", "red", "lightgreen", 
                                        "brown", "grey", "black", "white", "purple", "orange", "pink", "cyan", 
                                        "magenta", "lime", "teal", "indigo", "maroon", "navy", "olive", "silver", 
                                        "aqua", "fuchsia", "green"]
                }
            ]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "legend": {
                "display": False
            }
        }
    }
    
    return chart_data_power_mix

def get_chart_data_gpu_cpu(data, largest_task_length):
    chart_data = {
        "type": "line",
        "data": {
            "labels": [],
            "datasets": []
        },
        "options": {
            "maintainAspectRatio": False,
            "legend": {
                "display": True, 
                "labels": {
                    "fontStyle": "normal"
                }
            },
            "title": {
                "fontStyle": "normal"
            },
            "scales": {
                "xAxes": [
                    {
                        "gridLines": {
                            "color": "rgb(234, 236, 244)",
                            "zeroLineColor": "rgb(234, 236, 244)",
                            "drawBorder": False,
                            "drawTicks": False,
                            "borderDash": ["2"],
                            "zeroLineBorderDash": ["2"],
                            "drawOnChartArea": False
                        },
                        "ticks": {
                            "fontColor": "#858796",
                            "fontStyle": "normal",
                            "padding": 20
                        }
                    }
                ],
                "yAxes": [
                    {
                        "gridLines": {
                            "color": "rgb(234, 236, 244)",
                            "zeroLineColor": "rgb(234, 236, 244)",
                            "drawBorder": False,
                            "drawTicks": False,
                            "borderDash": ["2"],
                            "zeroLineBorderDash": ["2"]
                        },
                        "ticks": {
                            "fontColor": "#858796",
                            "fontStyle": "normal",
                            "padding": 20
                        }
                    }
                ]
            }
        }
    }

    colors = [
        "rgba(78, 115, 223, 0.05)",
        "rgba(223, 78, 115, 0.05)",
        "rgba(115, 223, 78, 0.05)",
        "rgba(223, 115, 78, 0.05)",
        "rgba(78, 223, 115, 0.05)",
        "rgba(115, 78, 223, 0.05)",
        "rgba(223, 223, 78, 0.05)",
        "rgba(78, 223, 223, 0.05)",
        "rgba(223, 78, 223, 0.05)",
        "rgba(115, 115, 223, 0.05)",
        "rgba(223, 115, 115, 0.05)",
        "rgba(115, 223, 223, 0.05)",
        "rgba(223, 223, 115, 0.05)",
        "rgba(78, 115, 78, 0.05)",
        "rgba(115, 78, 78, 0.05)",
        "rgba(223, 78, 223, 0.05)",
        "rgba(78, 223, 78, 0.05)",
        "rgba(223, 115, 223, 0.05)",
        "rgba(115, 223, 115, 0.05)",
        "rgba(223, 223, 223, 0.05)"
    ]

    for i, (label, dataset) in enumerate(data.items()):
        chart_data["data"]["datasets"].append({
            "label": label,
            "fill": True,
            "data": dataset,
            "backgroundColor": colors[i % len(colors)],
            "borderColor": colors[i % len(colors)].replace("0.05", "1"),
            "borderWidth": 3,
        })

    chart_data["data"]["labels"] = [i for i in range(1, largest_task_length + 1)]

    return chart_data

class Dashboard:
    def __init__(self):
        self.app = app
        self.db = db
    ### ROUTES ###
    @app.route('/receive_update', methods=['POST', 'GET'])
    def receive_update():
        """
        Receives update data and generates chart data for carbon tracking.

        Returns:
            JSON: A JSON object containing chart data for carbon tracking, energy consumption, carbon intensity, CO2 emissions,
                power mix, and GPU/CPU information.
        """
        data = request.get_json()
        #print("DATA", data)
        if any(not data_list for data_list in data.values()):
                return jsonify(chart_data_carb=get_chart_data({},0), chart_data_time=get_chart_data({},0), chart_data_inf=get_chart_data_inf([]), energy=0, 
                    carb_int=0, co2=0, chart_data_power_mix=get_chart_data_power_mix(get_power_mix()), chart_data_gpu_cpu=get_chart_data_gpu_cpu({}, 0))   
        
        tracking_info, carb_int, energy, co2, elapsed_time_info, train_info = get_carbon_data(data)
        inference_info_avg, elapsed_time_inf, inference_info  = get_inf_data(data)
        #_, _, power_mix = get_carbon_intensity()
        power_mix = get_power_mix()
        gpu_cpu_info = {}
        # Function to merge values
        def merge_values(d):
            for key, value in d.items():
                for v, h, g in value:
                    curr = f"{h}:{g}"
                    if curr in gpu_cpu_info:
                        gpu_cpu_info[curr].append((v))
                    else:
                        gpu_cpu_info[curr] = [(v)]

        # Apply the function to each dictionary
        merge_values(train_info)

        task_models = [item[2] for sublist in tracking_info.values() for item in sublist]
        try:
            _ ,max_length = Counter(task_models).most_common(1)[0]
        except IndexError:
            max_length = 0

        if max_length != 0:
            chart_data_carb = get_chart_data(tracking_info, max_length)
            chart_data_time = get_chart_data(elapsed_time_info, max_length)
            chart_data_gpu_cpu = get_chart_data_gpu_cpu(gpu_cpu_info, len(gpu_cpu_info[list(gpu_cpu_info.keys())[0]])) 
        else:
            chart_data_carb = get_chart_data({}, 0)
            chart_data_time = get_chart_data({}, 0)
            chart_data_gpu_cpu = get_chart_data_gpu_cpu({}, 0)
            
        chart_data_inf = get_chart_data_inf(inference_info_avg)
        chart_data_power_mix = get_chart_data_power_mix(power_mix)
        

        return jsonify(chart_data_carb=chart_data_carb, chart_data_time=chart_data_time, chart_data_inf=chart_data_inf, energy=energy, 
                    carb_int=carb_int*1000, co2=co2, chart_data_power_mix=chart_data_power_mix, chart_data_gpu_cpu=chart_data_gpu_cpu)
    
    @app.route('/')
    def index():
        """
        Renders the index.html template with the necessary data for the webpage.

        Returns:
            The rendered index.html template with the required data.
        """
        chart_data = get_chart_data({}, 0)
        chart_data_inf = get_chart_data_inf([])
        chart_data_power_mix = get_chart_data_power_mix(get_power_mix())

        
        _ , tasks, hostgpu, models = get_initial_data()
        unique_hosts = list(set(host.host for host in hostgpu))
        unique_tasks = list(set(task.task for task in tasks))

        return render_template('index.html', data={'track_info':{}, 'tasks':tasks, 'hostgpus':hostgpu, 'unique_hosts':unique_hosts, 'unique_tasks':unique_tasks, 'models': models,
                                                'labels':[], 'chart_data':chart_data, 'chart_data_inf':chart_data_inf, 'chart_data_power_mix':chart_data_power_mix})

    @app.route('/send_info', methods=['POST'])
    def receive_info():
        """
        Receives information from a POST request and processes it accordingly.
        
        If the received data contains 'hardware' key, it adds an initialization entry to the tracker
        and returns a JSON response with the task and device IDs.
        
        If the received data contains 'timestamp' key, it adds a training or inference entry to the tracker
        based on the 'mode' value and returns a JSON response indicating the success of data reception.
        
        If the received data does not contain 'hardware' or 'timestamp' key, it returns a JSON response
        indicating that the data was not received.
        """
        data = request.get_json()

        if 'hardware' in data:
            mode = data['mode']
            model = data['model']
            task = data['task']
            hardware = data['hardware']
            host = data['host']

            task, dev_ids = add_init_entry(mode=mode, model=model, task=task, hardware=hardware, host=host)

            return jsonify({"message": "Data received successfully", "task": task, "dev_ids": dev_ids})

        elif 'timestamp' in data:
            timestamp = data['timestamp']
            power_usage = data['energy_consumed']
            host = data['host']
            model = data['model']
            elapsed_time = data['time']
            task = data['task']
            hardware_distr = data['hardware_distr']
            dev_ids = data['dev_ids']
            start = data['start']

        else:
            return jsonify({"message": "Data not received"})
        
        if data["mode"] == "training":
            add_train_entry(carb_int=get_carbon_intensity()[0], power_usg=power_usage, CO2_usg=get_carbon_intensity()[0]*power_usage, 
                    task=task, timestamp=timestamp, elapsed_time=elapsed_time, model=model, dev_ids=dev_ids,hardware_distr=hardware_distr, start=start)

            return jsonify({"message": "Data received successfully"})

        elif data["mode"] == "inference":
            add_inference_entry(carb_int=get_carbon_intensity()[0], power_usg=power_usage, CO2_usg=get_carbon_intensity()[0]*power_usage, 
                        task=task, timestamp=timestamp, elapsed_time=elapsed_time, model=model, dev_ids=dev_ids, hardware_distr=hardware_distr)
            
            return jsonify({"message": "Data received successfully"})
        else:
            return jsonify({"message": "Data not received"})

    @app.route('/delete', methods=['GET'])
    def delete(task, model):
        """
        Deletes a task and model from the database.

        Args:
            task (str): The name of the task to delete.
            model (str): The name of the model to delete.

        Returns:
            str: A string indicating the success of the deletion.
        """
        task = Task.query.filter_by(task=task).first()
        model = Model.query.filter_by(model_name=model).first()
        db.session.delete(task)
        db.session.delete(model)
        db.session.commit()

        return "Task and model deleted successfully"

    def start(self):
        def update_power_mix():
            """
            Updates the power mix.
            """
            while True:
                _, _, power_mix = get_carbon_intensity()

                new_power_mix = Powermix(
                    timestamp=time.time(),
                    powermix=str(power_mix)
                )

                with app.app_context():
                    db.session.add(new_power_mix)
                    db.session.commit()

                time.sleep(3600)

        with app.app_context():
            db.create_all()

            update_power_mix = threading.Thread(target=update_power_mix, daemon=True)
            update_power_mix.start()

        app.run(debug=True, port=5001)



