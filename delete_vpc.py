import sys
import boto3
import os
import json
import time

#Need to change the environment variable of vpcid,it is called 'tt'
def lambda_handler(event, context)
    LLTD =json.loads(event["body"])
    vpcid = LLTD["vpcid"]
    """Remove VPC from AWS
    Set your region/access-key/secret-key from env variables or boto config.
    :param vpcid: id of vpc to delete
    """
    if not vpcid:
        return
    print('Removing VPC ({}) from AWS'.format(vpcid))
    ec2 = boto3.resource('ec2')
    ec2client = ec2.meta.client
    vpc = ec2.Vpc(vpcid)
    a = ec2client.describe_nat_gateways(
        Filters=[ 
            {
            'Name': 'vpc-id',
            'Values': [
                vpcid
            ]
        }
        ]
        )
    for n in a['NatGateways']:
        natgatewayid = n['NatGatewayId']
        ec2client.delete_nat_gateway( NatGatewayId=natgatewayid)
    time.sleep(60)
    # detach and delete all gateways associated with the vpc
    for gw in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=gw.id)
        gw.delete()
    # delete all route table associations
    for rt in vpc.route_tables.all():
        for rta in rt.associations:
            if not rta.main:
                rta.delete()
        response_main = ec2client.describe_route_tables(
        Filters=[
            {
                'Name': 'association.main',
                'Values': [
                    'true'
                ]
            },
            {
                'Name': 'vpc-id',
                'Values': [
                    vpcid
                ]
            }
        ]
    )
    MainRouteTableId = response_main['RouteTables'][0]['RouteTableId']
    response = ec2client.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpcid
                ]
            }
        ]
    )
    for i  in response['RouteTables']:
        RouteTableId = i['RouteTableId']
        if RouteTableId != MainRouteTableId:
            ec2client.delete_route_table(RouteTableId=RouteTableId)

    # delete any instances
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            instance.terminate()
    # delete our endpoints
    for ep in ec2client.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        ec2client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
    # delete our security groups
    for sg in vpc.security_groups.all():
        if sg.group_name != 'default':
            sg.delete()
    # delete any vpc peering connections
    for vpcpeer in ec2client.describe_vpc_peering_connections(
            Filters=[{
                'Name': 'requester-vpc-info.vpc-id',
                'Values': [vpcid]
            }])['VpcPeeringConnections']:
        ec2.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()
    # delete non-default network acls
    for netacl in vpc.network_acls.all():
        if not netacl.is_default:
            netacl.delete()
    # delete network interfaces
    for subnet in vpc.subnets.all():
        for interface in subnet.network_interfaces.all():
            interface.delete()
        subnet.delete()
    # finally, delete the vpc
    ec2client.delete_vpc(VpcId=vpcid)


def main(argv=None):
    vpc_cleanup(argv[1])


if __name__ == '__main__':
    main(sys.argv)
    
