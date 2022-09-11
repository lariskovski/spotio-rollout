import requests
import json

BASE_URL="https://api.spotinst.io/ocean/aws/k8s"
API_TOKEN = ""
AMI = ""

def get_clusters() -> list:
    response = requests.get(f"{BASE_URL}/cluster", headers=header).json()
    clusters = []
    for cluster in response['response']['items']:
        clusters.append({"name": cluster['name'], "id": cluster['id'], "imageId": cluster['compute']['launchSpecification']['imageId']})
    return clusters

def get_cluster_launch_spec_id(ocean_cluster_id) -> list:
    response = requests.get(f"{BASE_URL}/cluster/{ocean_cluster_id}/nodes", headers=header).json()
    launch_spec_ids = []
    for node in response['response']['items']:
        if node['launchSpecName'] != "Default":
            node_launch_spec_id = node['launchSpecId']
            if node_launch_spec_id not in launch_spec_ids:
                launch_spec_ids.append(node_launch_spec_id)
        else:
            print("Default VNG doesn't have LaunchSpecID. Try updating the cluster imageId directly.")
    return launch_spec_ids

def update_vng_image(ocean_launch_spec_id, ami) -> dict:
    # update_vng = f"{BASE_URL}/launchSpec/{oceanLaunchSpecId}"
    body = {"launchSpec":{"imageId":ami}}
    response = requests.put(f"{BASE_URL}/launchSpec/{ocean_launch_spec_id}", data=json.dumps(body), headers=header).json()
    return response['response']


def initiate_roll(ocean_cluster_id, batch_size_percentage=20, batch_min_healthy_percentage=70, respect_disruption_budget=True):
    # https://spot.io/blog/use-oceans-cluster-roll-to-update-nodes/
    # https://docs.spot.io/api/#operation/oceanAwsRollInit
    body = {
        "roll": {
        "batchSizePercentage": batch_size_percentage,
        "comment": "Update EKS version.",
        "respectPdb": respect_disruption_budget,
        "batchMinHealthyPercentage": batch_min_healthy_percentage
        }
    }
    response = requests.post(f"{BASE_URL}/cluster/{ocean_cluster_id}/roll", data=json.dumps(body), headers=header).json()
    return response['response']

def update_cluster(ocean_cluster_id, ami):
    # Update cluster imageId - same as VNG defautl group - so it matches the updated VNG.
    body = {"cluster": {"compute": {"launchSpecification": {"imageId": ami}}}}
    response = requests.put(f"{BASE_URL}/cluster/{ocean_cluster_id}", data=json.dumps(body), headers=header).json()
    return response['response']

if __name__ == "__main__":
    # Organizations with Multiple Accounts
    # Each API call you make should be appended to the account ID. For example:
    # spotinst= f"https://api.spotinst.io/aws/ec2/group?accountId={account_id}"

    header = {"Authorization": f"Bearer {API_TOKEN}", 'Content-Type': 'application/json'}
    clusters = get_clusters()

    TARGET = "test-cluster"
    
    for cluster in clusters:
        current_image = cluster["imageId"]
        if cluster["name"] == TARGET and current_image != AMI:
            cluster_id = cluster["id"]
            launch_spec = get_cluster_launch_spec_id(cluster_id)[0]
            # print(get_clusters()[0])
            # print(cluster_id)
            # print(launch_spec)
            vng_confirmation = input(f"Confirm VNG imageId update from [{current_image}] to [{AMI}] (y): ")
            if vng_confirmation.lower() == "y":
                print(update_vng_image(launch_spec, AMI))
                roll_confirmation = input(f"Confirm rollout initialization (y): ")
                if roll_confirmation.lower() == "y":
                    print(initiate_roll(cluster_id))
                    print(update_cluster(cluster_id, AMI))
        else:
            print("Image already up to date.")
