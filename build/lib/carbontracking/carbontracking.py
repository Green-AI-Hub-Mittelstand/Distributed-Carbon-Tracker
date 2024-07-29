import requests
import time
import threading
from .codecarbon.emissions_tracker import EmissionsTracker
import json
import socket
from .hardware import CPU, GPU, RAM, AppleSiliconChip
from collections import Counter
from .cpu import *
from .gpu import *
from .powermetrics import *
import os

class MacEmmissionTracker():
    """
    A class for tracking energy consumption of hardware devices.

    Attributes:
        energy (float): The total energy consumption.
        energy_distr (dict): A dictionary representing the distribution of energy consumption.
        hardware (list): A list of hardware devices being tracked.
        last_duration (int): The duration of the last measurement.
        output_dir (str): The directory to store the measurement results.

    Methods:
        flush(): Measures the power and energy consumption of the tracked hardware devices.
    """
    def __init__(self, last_duration=1, dashboard=False):
        """
            Initializes a CarbonTracker object.

            Args:
                last_duration (int): The duration of the last recorded energy consumption in hours. Defaults to 1.
        """
        
        self.dash = dashboard
        self.energy = 0
        self.energy_distr = {}
        self.hardware = []
        self.last_duration = last_duration
        self.output_dir = "output_dir"
        #self.carbon_intensity = get_carbon_intensity()
        self.carbon_intensity = 0.0005

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if is_gpu_details_available():
            gpu_devices = GPU.from_utils(GPU._get_gpu_ids)
            self.hardware.append(gpu_devices)
            gpu_names = [n["name"] for n in gpu_devices.devices.get_gpu_static_info()]
            gpu_names_dict = Counter(gpu_names)


        if is_powergadget_available():
            hardware = CPU.from_utils(self.output_dir, "intel_power_gadget")
            self.hardware.append(hardware)
        elif is_rapl_available():
            hardware = CPU.from_utils(self.output_dir, "intel_rapl")
            self.hardware.append(hardware)
        elif (
            is_powermetrics_available()
        ):
            print("Using powermetrics for CPU power tracking.")
        hardware_cpu = AppleSiliconChip.from_utils(
            self.output_dir, chip_part="CPU"
        )
        self.hardware.append(hardware_cpu)

        hardware_gpu = AppleSiliconChip.from_utils(
            self.output_dir, chip_part="GPU"
        )
        self.hardware.append(hardware_gpu)

        print(self.hardware)

        for hw in self.hardware:
            hw.start()
        
    def send_data(self):
        """
        Send tracking data to the server.
        """
        url = "http://127.0.0.1:5001/send_info"
        response = requests.post(url, json=self.data)
        
        try:
            if response.json()["task"] != None:
                self.task = response.json()["task"]
                self.dev_ids = response.json()["dev_ids"]
        except KeyError:
            pass

        # Check response status
        if response.status_code == 200:
            print("Data sent successfully!")
        else:
            print("Failed to send data.")

    def flush(self):
        """
            Flushes the data and calculates the CO2 emissions for each hardware component.

            Returns:
                dict: A dictionary containing the CO2 emissions for each hardware component.
        """
        result = {}
        co2_emissions = {}
        for hw in self.hardware:
            res = hw.measure_power_and_energy(self.last_duration)
            if "cpu" in str(hw).lower():
                result[str(hw)] = res 
            elif "gpu" in str(hw).lower():
                result[str(hw)] = res
        
        print(result)
        for key, value in result.items():
            #print(result[key][1].kWh)
            co2_emissions[key] = value[1].kWh * self.carbon_intensity
        
        if self.dash:
            self.data = {
                "timestamp" : time.time(),
                "energy_consumed": (result["cpu"][1].kWh, result["gpu"][1].kWh),
                "host": 'test_host',
                "task": 'test_task',
                "model": 'test_model',
                "time": self.time,
                "hardware_distr": self.energy_distr,
                "dev_ids": self.dev_ids,
                "start": self.start,
                "mode": self.mode
            }

        return co2_emissions





class EmissionTracker:
    """
    A helper class for tracking emissions and sending data to a server.

    Attributes:
        data (dict): A dictionary to store tracking data.
        dev_ids (list): A list of device IDs.
        power_usg (int): The power usage.
        nvml (bool): Flag indicating if NVML is enabled.
        gpu (bool): Flag indicating if GPU is enabled.
        tracker (EmissionsTracker): An instance of the EmissionsTracker class.
        tracking_info (int): Tracking information.
        running (bool): Flag indicating if tracking is running.
        task (str): The task being tracked.
        hostname (str): The hostname of the client.
        mode (str): The mode of tracking.
        start (bool): Flag indicating if tracking has started.
        time (int): The elapsed time.
        time_start (int): The start time of tracking.

    Methods:
        start_tracking: Start tracking emissions.
        stop_tracking: Stop tracking emissions.
        flushing_thread: Thread for flushing tracking data.
        send_data: Send tracking data to the server.
        flush: Flush tracking data.
    """

    def __init__(self, task="track_new", GPU=False, dashboard=True):
        """
        Initializes a new instance of the ClientHelper class.

        Args:
            task (str, optional): The task to be tracked. Defaults to "track_new".
            GPU (bool, optional): Flag indicating if GPU is enabled. Defaults to False.
        """
        self.data = {}
        self.dev_ids = []
        self.power_usg = 0
        self.nvml = False
        self.gpu = GPU
        self.tracker = EmissionsTracker(save_to_file=False)
        self.tracking_info = 0
        self.running = True
        self.task = task
        self.hostname = socket.gethostname()
        self.mode = "training"
        self.start = True
        self.time = 0
        self.time_start = 0
        self.total_energy_cpu = 0
        self.total_energy_gpu  = 0
        self.dashboard = dashboard

        if not self.dashboard:
            self.carbon_intensity = get_carbon_intensity()

    def start_tracking(self, task, model, mode="training"):
        """
        Start tracking emissions.

        Args:
            task (str): The task to be tracked.
            model: The model being used.
            mode (str, optional): The mode of tracking. Defaults to "training".

        Raises:
            ValueError: If an invalid mode is provided.
        """
        valid_values = {'training', 'inference'}
        
        if mode.lower() not in valid_values:
            raise ValueError('Invalid input. The value must be either "training" or "inference".')
        
        self.task = task
        self.model = model
        self.mode = mode
        self.start = True
        hardware = self.tracker.get_hardware()
        hardware = [str(h) for h in hardware]


        self.data = {"task": self.task, "model": self.model, "mode": self.mode, "hardware": hardware, 'host': self.hostname}

        if self.dashboard:
            self.send_data()

        self.tracker.start()

        self.time_start = time.time()

        
        """if self.dashboard:
            self.flushing = threading.Thread(target=self.flushing_thread, daemon=True)
            self.flushing.start()"""


    def stop_tracking(self):
        """
        Stop tracking emissions.
        """
        self.tracker.stop()
        self.running = False

        if self.flushing is not None:
            self.flushing.join()


    def flushing_thread(self):
        """
        Thread for flushing tracking data.
        """
        if self.mode != "inference":
            while self.running:
                print("Flushing...")
                self.flush()
        
    def send_data(self):
        """
        Send tracking data to the server.
        """
        url = "http://127.0.0.1:5001/send_info"
        response = requests.post(url, json=self.data)
        
        try:
            if response.json()["task"] != None:
                self.task = response.json()["task"]
                self.dev_ids = response.json()["dev_ids"]
        except KeyError:
            pass

        # Check response status
        if response.status_code == 200:
            print("Data sent successfully!")
        else:
            print("Failed to send data.")
    
    def flush(self):
        """
        Flush tracking data.
        
        Returns:
            int: The energy consumed during the flush.
        """
        self.tracking_info, self.energy_distr, self.total_energy_cpu, self.total_energy_gpu = self.tracker.flush()
        self.tracking_info = json.loads(self.tracking_info.toJSON())
        self.time += time.time() - self.time_start
        self.time_start = time.time()
        
        print(self.total_energy_cpu, self.total_energy_gpu)
        for key, value in self.energy_distr.items():
            if "cpu" in str(key).lower():
                self.energy_distr[key] = self.total_energy_cpu.kWh
            elif "gpu" in str(key).lower():
                self.energy_distr[key] = self.total_energy_gpu.kWh
        
        print("NEW", self.energy_distr)

        self.data = {
            "timestamp" : self.tracking_info["timestamp"],
            "energy_consumed": self.tracking_info["energy_consumed"],
            "host": self.hostname,
            "task": self.task,
            "model": self.model,
            "time": self.time,
            "hardware_distr": self.energy_distr,
            "dev_ids": self.dev_ids,
            "start": self.start,
            "mode": self.mode
        }


        if self.dashboard:
            self.send_data()
        else:
            return self.tracking_info["energy_consumed"], self.carbon_intensity

        self.start = False

        return self.tracking_info["energy_consumed"]

def get_carbon_intensity(time_dur=None):
    """
    Calculate the carbon intensity of electricity generation in a specific country.

    Args:
        time_dur (optional): The duration of time to query the electricity generation data. Defaults to None.

    Returns:
        tuple: A tuple containing the carbon intensity in kilograms of CO2 per kilowatt-hour (kgCO2/kWh),
               the address of the data source, and the power mix dictionary.

    """

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
    
    return carbon_intensity/1000, "address", power_mix


