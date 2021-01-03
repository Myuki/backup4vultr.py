import json
import re
import requests
import sys
import time


class Vultr:
  apiToken: str
  instanceMeta: dict
  instanceList: list
  snapshotMeta: dict
  snapshotList: list

  httpHeaders: dict = {"Content-Type": "application/json"}
  retries: int = 3  # Retry 3 times
  timeout: int = 5

  def __init__(self, apiToken: str):
    # Check the API token and init vultr object
    if apiToken == "":
      print("API Token is empty")
      sys.exit(1)
    self.apiToken = apiToken
    self.httpHeaders["Authorization"] = "Bearer " + apiToken

  # Check Instances ID
  def checkInstancesID(self, inputInstancesID):
    if "instanceList" not in dir(self):
      self.getInstanceList()
    instanceID: bool = False
    for instance in self.instanceList:
      if inputInstancesID == instance["id"]:
        instanceID = True
    if instanceID == False:
      print("Instances ID is wrong, this is instance list:")
      self.listInstances()
      sys.exit(1)

  # Get the instance list
  # curl --location --request GET 'https://api.vultr.com/v2/instances' --header 'Authorization: Bearer {api-key}'
  def getInstanceList(self):
    # Retry 3 times
    for i in range(self.retries):
      try:
        r = requests.get("https://api.vultr.com/v2/instances", headers=self.httpHeaders, timeout=self.timeout)
      except Exception as e:
        print(e)
        print("Error, try again after 3s")
        time.sleep(3)
      else:
        # Check respond
        if r.status_code == 200:
          instances: dict = json.loads(r.text)
          self.instanceMeta = instances["meta"]
          self.instanceList = instances["instances"]
        else:
          print("Fail to get instance list")
          if r.status_code == 400:
            print("400 Bad Request")
          elif r.status_code == 401:
            print("401 Unauthorized")
          elif r.status_code == 403:
            print("403 Forbidden")
          elif r.status_code == 404:
            print("404 Not Found")
          else:
            print(r.status_code, "Unknown Error")
          print(r.text)
          sys.exit(1)
        break

  # List all instances
  def listInstances(self):
    if "instanceList" not in dir(self):
      self.getInstanceList()
    print("Instance List:")
    print("ID                                   Label RAM  Main IP")
    for instance in self.instanceList:
      print(instance["id"], instance["label"], instance["ram"], instance["main_ip"])

  # Get the snapshot list
  # curl --location --request GET "https://api.vultr.com/v2/snapshots" --header "Authorization: Bearer {api-key}"
  def getSnapshotList(self):
    # Retry 3 times
    for i in range(self.retries):
      try:
        r = requests.get("https://api.vultr.com/v2/snapshots", headers=self.httpHeaders, timeout=self.timeout)
      except Exception as e:
        print(e)
        print("Error, try again after 3s")
        time.sleep(3)
      else:
        # Check respond
        if r.status_code == 200:
          snapshots: dict = json.loads(r.text)
          self.snapshotMeta = snapshots["meta"]
          self.snapshotList = snapshots["snapshots"]
        else:
          print("Fail to get snapshot list")
          if r.status_code == 401:
            print("401 Unauthorized")
          else:
            print(r.status_code, "Unknown Error")
          print(r.text)
          sys.exit(1)
        break

  # List all snapshots
  def listSnapshots(self):
    if "snapshotList" not in dir(self):
      self.getSnapshotList()
    print("Snapshot List:")
    print("ID                                   Size        Created Date              Status   Description")
    for instance in self.snapshotList:
      print(instance["id"], instance["size"], instance["date_created"], instance["status"], instance["description"])

  # Mark keeped snapshot in List
  def markKeepedSnapshot(self, id: str):
    if "snapshotList" not in dir(self):
      self.getSnapshotList()
    for snapshot in self.snapshotList:
      if id in snapshot["id"]:
        snapshot["keepedFlag"] = 1

  # Get the oldest snapshot ID
  # Format: yyyy-mm-ddThh:mm:ss+00:00
  def getOldestSnapshot(self) -> str:
    if "snapshotList" not in dir(self):
      self.getSnapshotList()
    timeRegex = r"^(\d{4})-(\d\d)-(\d\d)T(\d\d)\:(\d\d)\:(\d\d)"
    result = re.match(timeRegex, time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time())))
    oldestDate: list = (result.group(0), result.group(1), result.group(2), result.group(3), result.group(4), result.group(5))
    # Compare all snapshots
    for snapshot in self.snapshotList:
      if "keepedFlag" not in snapshot:
        result = re.match(timeRegex, snapshot["date_created"])
        for i in range(6):
          # Compare time
          if result.group(i) < oldestDate[i]:
            oldestID = snapshot["id"]
            oldestDate = (result.group(0), result.group(1), result.group(2), result.group(3), result.group(4), result.group(5))
            break
    return oldestID

  # Create new snapshot for specific VM
  # curl --location --request POST "https://api.vultr.com/v2/snapshots" --header "Authorization: Bearer {api-key}" --header "Content-Type: application/json" --data-raw "{"instance_id": 38863911, "description" : "my snapshot"}"
  def createSnapshot(self, instanceID: str, description: str = ""):
    payload = {"instance_id": instanceID, "description": description}
    # Retry 3 times
    for i in range(self.retries):
      try:
        r = requests.post("https://api.vultr.com/v2/snapshots", headers=self.httpHeaders, data=json.dumps(payload), timeout=self.timeout)
      except Exception as e:
        print(e)
        print("Error, try again after 3s")
        time.sleep(3)
      else:
        # Check respond
        if r.status_code == 201:
          print("Create snapshot success")
        else:
          print("Fail to create snapshot")
          if r.status_code == 400:
            print("400 Bad Request")
          elif r.status_code == 401:
            print("401 Unauthorized")
          else:
            print(r.status_code, "Unknown Error")
          print(r.text)
          sys.exit(1)
        break

  # Delete snapshot
  # curl --location --request DELETE "https://api.vultr.com/v2/snapshots/{snapshot-id}" --header "Authorization: Bearer {api-key}"
  def deleteSnapshot(self, snapshotID: str):
    if "snapshotList" not in dir(self):
      self.getSnapshotList()
    # Retry 3 times
    for i in range(self.retries):
      try:
        r = requests.delete("https://api.vultr.com/v2/snapshots/" + snapshotID, headers=self.httpHeaders, timeout=self.timeout)
      except Exception as e:
        print(e)
        print("Error, try again after 3s")
        time.sleep(3)
      else:
        # Check respond
        if r.status_code == 204:
          # Delete in snapshot list
          for i in range(len(self.snapshotList)):
            deletedSnapshot: dict = self.snapshotList[i]
            if snapshotID == deletedSnapshot["id"]:
              del self.snapshotList[i]
              self.snapshotMeta["total"] -= 1
              break
          print("Delete snapshot success")
        else:
          print("Fail to delete snapshot")
          if r.status_code == 400:
            print("400 Bad Request")
          elif r.status_code == 401:
            print("401 Unauthorized")
          elif r.status_code == 404:
            print("404 Not Found")
          else:
            print(r.status_code, "Unknown Error")
          print(r.text)
          sys.exit(1)
        break

  # Backup instance
  def backup(self, instanceID: str, configSnapshotsLimit: int = 10, keepedSnapshotList: tuple = ()):
    # Check the instance ID
    self.checkInstancesID(instanceID)

    # Check the limit of snapshot
    snapshotLimit: int = 10 - len(keepedSnapshotList)
    # Check the available limit
    if snapshotLimit < 1:
      print("Snapshots reach the limit")
      print("Please remove at least %d in keepedSnapshotList." % (snapshotLimit + 1))
      sys.exit(1)
    # If config limit < 0 means no limit
    if configSnapshotsLimit < 0:
      print("configSnapshotsLimit < 0, use %d as the limit." % snapshotLimit)
    elif configSnapshotsLimit == 0:
      print("configSnapshotsLimit = 0, exit")
      sys.exit(0)
    elif configSnapshotsLimit > 0 and configSnapshotsLimit < snapshotLimit:
      snapshotLimit = configSnapshotsLimit
    # If config limit > available limit, use available limit
    elif configSnapshotsLimit > snapshotLimit:
      print("Config snapshots limit exceed the available limit")
      print("Fallback use %d as the limit." % snapshotLimit)

    # Mark the snapshot need be keeped
    for keepedSnapshot in keepedSnapshotList:
      self.markKeepedSnapshot(keepedSnapshot)

    # Delete the oldest snapshot if reach the snapshot limit
    snapshotTotal: int = self.snapshotMeta["total"]
    while snapshotTotal >= snapshotLimit:
      self.deleteSnapshot(self.getOldestSnapshot())
      snapshotTotal = self.snapshotMeta["total"]

    # Create snapshot
    self.createSnapshot(instanceID)