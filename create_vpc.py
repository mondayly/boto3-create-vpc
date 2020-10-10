import json
import boto3
import time

def lambda_handler(event, context):
    #print (event)
    #print(type(event["body"]))
    LLTD =json.loads(event["body"])
    #Convert str to dict
    LLTD1 = LLTD["LLTD"]
    #print (type(LLTD1))
    #return event
    LLTD2 = LLTD["LLTD2"]
    LLTD3 = LLTD["LLTD3"]
    LLTD4 = LLTD["LLTD4"]
    LLTD5 = LLTD["LLTD5"]
    add = event["multiValueQueryStringParameters"]
    address = add["address"]
    #使用Postman中的Params，添加键值对，Key和Value都可以自定义，再通过event引用
    ec2 = boto3.resource('ec2')
    vpc = ec2.create_vpc(CidrBlock=address[0])
    vpc.create_tags(Tags=[{"Key": "Name", "Value": LLTD1}])
    vpc.wait_until_available()
    ec2Client = boto3.client('ec2')
    ec2Client.modify_vpc_attribute( VpcId = vpc.id , EnableDnsSupport = { 'Value': True } )
    ec2Client.modify_vpc_attribute( VpcId = vpc.id , EnableDnsHostnames = { 'Value': True } )
    internetgateway = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId = internetgateway.id)
    routetable1 = vpc.create_route_table()
    route1 = routetable1.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=internetgateway.id)
    routetag1 = routetable1.create_tags(Tags=[{"Key":"Name","Value":"public_route_table"}])
    subnet1 = ec2.create_subnet(AvailabilityZone="us-east-2a",CidrBlock=LLTD2, VpcId=vpc.id)
    ec2Client.associate_route_table(RouteTableId=routetable1.id,SubnetId=subnet1.id)
    subnet2 = ec2.create_subnet(AvailabilityZone="us-east-2a",CidrBlock=LLTD3, VpcId=vpc.id)
    subnet3 = ec2.create_subnet(AvailabilityZone="us-east-2b",CidrBlock=LLTD4, VpcId=vpc.id)
    subnet4 = ec2.create_subnet(AvailabilityZone="us-east-2b",CidrBlock=LLTD5, VpcId=vpc.id)
    ec2Client.associate_route_table(RouteTableId=routetable1.id,SubnetId=subnet4.id)
    ec2Client.modify_subnet_attribute(MapPublicIpOnLaunch={ 'Value': True},SubnetId=subnet1.id)
    ec2Client.modify_subnet_attribute(MapPublicIpOnLaunch={ 'Value': True},SubnetId=subnet4.id)
    subnet1tag = subnet1.create_tags(Tags=[{"Key":"Name","Value":"Public_Subnet1"}])
    subnet2tag = subnet2.create_tags(Tags=[{"Key":"Name","Value":"Private_Subnet1"}])
    subnet3tag = subnet3.create_tags(Tags=[{"Key":"Name","Value":"Private_Subnet2"}])
    subnet4tag = subnet4.create_tags(Tags=[{"Key":"Name","Value":"Public_Subnet2"}])
    elasticip1 = ec2Client.allocate_address()
    elasticip2 = ec2Client.allocate_address()
    natgateway1 = ec2Client.create_nat_gateway(AllocationId=elasticip1['AllocationId'],SubnetId=subnet1.id)
    natgateway2 = ec2Client.create_nat_gateway(AllocationId=elasticip2['AllocationId'],SubnetId=subnet4.id)
    time.sleep(20)
    routetable2 = vpc.create_route_table()
    route2 = routetable2.create_route(DestinationCidrBlock='0.0.0.0/0', NatGatewayId=natgateway1['NatGateway']['NatGatewayId'])
    routetag2 = routetable2.create_tags(Tags=[{"Key":"Name","Value":"private_route_table1"}])
    ec2Client.associate_route_table(RouteTableId=routetable2.id,SubnetId=subnet2.id)
    routetable3 = vpc.create_route_table()
    route3 = routetable3.create_route(DestinationCidrBlock='0.0.0.0/0', NatGatewayId=natgateway2['NatGateway']['NatGatewayId'])
    routetag3 = routetable3.create_tags(Tags=[{"Key":"Name","Value":"private_route_table2"}])  
    ec2Client.associate_route_table(RouteTableId=routetable3.id,SubnetId=subnet3.id)
    
    return "success"
