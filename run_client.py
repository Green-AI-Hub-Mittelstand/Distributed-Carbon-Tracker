from carbontracking import EmissionTracker, MacEmmissionTracker, Dashboard
import time


"""client = MacEmmissionTracker(last_duration=20)   

for i in range(100):
    #time.sleep(5)
    out = client.flush()
    print(out)"""

client = EmissionTracker()
client.start_tracking("task", "model", "training")

for i in range(20):
    time.sleep(1)
    out = client.flush()
