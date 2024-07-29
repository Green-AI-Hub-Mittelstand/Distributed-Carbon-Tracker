from carbontracking import EmissionTracker, MacEmmissionTracker, Dashboard
import time


"""client = MacEmmissionTracker()   

for i in range(100):
    time.sleep(1)
    out = client.flush()
    print(out)
    break

client = EmissionTracker()
client.start_tracking("task", "model", "training")

for i in range(10):
    time.sleep(1)


client.stop_tracking()"""

dash = Dashboard()
dash.start()
