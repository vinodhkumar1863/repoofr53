import boto3

# Create a VPC
ec2 = boto3.resource('ec2')
vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
vpc.create_tags(Tags=[{"Key": "Name", "Value": "MyVPC"}])
vpc.wait_until_available()

# Enable DNS resolution and DNS hostname for the VPC
client = boto3.client('ec2')
client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsSupport={'Value': True})
client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsHostnames={'Value': True})

# Create internet gateway and attach it to the VPC
igw = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=igw.id)

# Create public subnet in the first Availability Zone (AZ)
subnet_public_1 = vpc.create_subnet(CidrBlock='10.0.0.0/24', AvailabilityZone='your-AZ-1')

# Create private subnets in the second Availability Zone (AZ)
subnet_private_1 = vpc.create_subnet(CidrBlock='10.0.10.0/24', AvailabilityZone='your-AZ-2')
subnet_private_2 = vpc.create_subnet(CidrBlock='10.0.11.0/24', AvailabilityZone='your-AZ-3')


# Create a route table for the public subnet and associate it
route_table_public = vpc.create_route_table()
route_table_public.associate_with_subnet(SubnetId=subnet_public_1.id)

# Create a route table for the private subnets and associate them
route_table_private = vpc.create_route_table()
route_table_private1.associate_with_subnet(SubnetId=subnet_private_1.id)
route_table_private2.associate_with_subnet(SubnetId=subnet_private_2.id)

# Add routes to the route tables
route_table_public.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=igw.id)  # Connect public subnet to internet gateway

route_table_private1.create_route(DestinationCidrBlock='10.0.10.0/24')

route_table_private2.create_route(DestinationCidrBlock='10.0.11.0/24')

# Create a security group


sec_group = ec2.create_security_group(
    Description='Security group for EC2 instance',
    GroupName='my-security-group',
    VpcId=vpc.id)

#Ingress Rule for SSH access 
sec_group.authorize_ingress(GroupId = sec_group.id ,
                IpPermissions=[
               {          
                'FromPort': 22, 'ToPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    { 
                            'CidrIp': '0.0.0.0/0',
                            'Description': 'SSH Access'
                    },],
                
},
])

#Ingress Rule for on-premise access
sec_group.authorize_ingress(GroupId = sec_group.id ,
                IpPermissions=[
            {          
                'FromPort': -1,'ToPort': -1,
                },
                'IpProtocol': 'icmp',
                'IpRanges': [
                { 
                    'CidrIp': '192.168.0.0/16',
                    'Description': 'Ping from On-Premise'
                },],

                },
                ])

#creating EC2 instance in public subnet 
instance = ec2.run_instances(ImageId='ami-id', 
                InstanceType='t2.micro' , 
                MinCount=1, 
                MaxCount=1, 
                NetworkInterfaces= [{ 'SubnetId':subnet_public_1 , 'SecurityGroupIds':'[sec_group.id]'}]
                TagSpecifications=[
                                    {
                'ResourceType': 'instance',
                'Tags': [
                    {
                    'Key': 'Purpose',
                    'Value': 'test',
                        },
                        ],
                                }
                            ],)








ec2 = boto3.client('ec2')

#create virtual private gateway
vgw=ec2.create_vpn_gateway(
AvailabilityZone='your-AZ-1',
Type='ipsec.1',
TagSpecifications=[
    {
        'ResourceType': 'vpn-gateway',
        'Tags': [
            {
                'Key': 'Name',
                'Value': 'MyVpnGateway'
            },
        ]
    },
],
)

#attach virtual private gateway(vgw) to vpc
attach_vpn_gateway=ec2.attach_vpn_gateway(
VpcId='VpcId',
VpnGatewayId='vgw.id'
)

#create customer gateway
customer_gateway=ec2.create_customer_gateway(
PublicIp='11.11.11.11',
Type='ipsec.1',
TagSpecifications=[
    {
        'ResourceType': 'customer-gateway',
        'Tags': [
            {
                'Key': 'Name',
                'Value': 'MyCustomerGateway'
            },
        ]
    },
],
)

#create site-to-site vpn connection
vpn_connection=ec2.create_vpn_connection(
    CustomerGatewayId='customer_gateway_id',
    Type='ipsec.1',
    VpnGatewayId='vgw.id',
    Options={
        'StaticRoutesOnly':True,
        'TunnelInsideIpVersion': 'ipv4',
        'TunnelOptions':[
            {
                'TunnelInsideCidr':'198.162.0.0/16',
                'PreSharedKey': 'pre_shared_key'
            }
        ]
    }
)

response = ec2.create_vpn_connection_route(
    DestinationCidrBlock='198.162.0.0/16',
    VpnConnectionId='vpn_connection.id'
)




# Allow SSH from 0.0.0.0/0
ec2.authorize_security_group_ingress(
    GroupId=security_group_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ]
)

# Allow ICMP from 192.168.0.0/16
ec2.authorize_security_group_ingress(
    GroupId=security_group_id,
    IpPermissions=[
        {
            'IpProtocol': 'icmp',
            'FromPort': -1,
            'ToPort': -1,
            'IpRanges': [{'CidrIp': '192.168.0.0/16'}]
        }
    ]
)


route53 = boto3.client('route53')

# Create a private hosted zone
response = route53.create_hosted_zone(
    Name='cloud.com',
    VPC={
        'VPCRegion': 'your-region',
        'VPCId': 'your-vpc-id'
    },
    CallerReference=str(time.time())  # Use timestamp as a unique reference
)

hosted_zone_id = response['HostedZone']['Id']


# Get the private IP address of the EC2 instance
response = ec2.describe_instances(InstanceIds=[instance.id])
private_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']

# Create an A record in the hosted zone
response = route53.change_resource_record_sets(
    HostedZoneId=hosted_zone_id,
    ChangeBatch={
        'Changes': [
            {
                'Action': 'CREATE',
                'ResourceRecordSet': {
                    'Name': 'app.cloud.com',
                    'Type': 'A',
                    'TTL': 300,
                    'ResourceRecords': [{'Value': private_ip}]
                }
            }
        ]
    }
)


route53 = boto3.client('route53')

# Create the security group for the Route53 resolver inbound endpoint
resolver_inbound_sg = ec2.create_security_group(
    GroupName='route53-resolver-inbound-sg',
    Description='Security group for Route 53 resolver inbound endpoint',
    VpcId=vpc.id
)

# Authorize DNS traffic from 192.168.0.0/16
resolver_inbound_sg.authorize_ingress(
    IpPermissions=[
        {
            'IpProtocol': 'udp',
            'FromPort': 53,
            'ToPort': 53,
            'IpRanges': [{'CidrIp': '192.168.0.0/16'}]
        }
    ]
)

#create route53 resolver inbound endpoint for private subnet-1
route53_resolver_inbound_1 =boto3.client('route53resolver')
route53_resolver.create_resolver_endpoint(CreatorRequestId='27-02-2024',
                                          SecurityGroupIds=[
                                                              'resolver_inbound_sg.id',
                                                            ],
                                          Direction='INBOUND',
                                          IpAddresses=[
                                                          {
                                                               'SubnetId': 'subnet_private_1',
                                                           },
    
                                                   ], )

#create route53 resolver inbound endpoint for private subnet-2
route53_resolver_inbound_2=boto3.client('route53resolver')
route53_resolver.create_resolver_endpoint(CreatorRequestId='27-02-2024',
                                          SecurityGroupIds=[
                                                              'resolver_inbound_sg.id',
                                                            ],
                                          Direction='INBOUND',
                                          IpAddresses=[
                                                          {
                                                               'SubnetId': 'subnet_private_2',
                                                           },
                                                       ], )

 




# Create the Route53 resolver inbound endpoint for the first private subnet
response_subnet1 = route53.create_resolver_rule(
    CreatorRequestId='subnet1-resolver-inbound',
    DomainName='cloud.com', 
    RuleType='FORWARD',
    Name='subnet1-resolver-inbound',
    TargetIps=[
        {
            'Ip': 'ip-address-of-destination',  # Replace with the actual IP address
            'Port': 53
        }
    ],
    ResolverEndpointId='resolver-endpoint-id-of-subnet1'
)

# Create the Route53 resolver inbound endpoint for the second private subnet
response_subnet2 = route53.create_resolver_rule(
    CreatorRequestId='subnet2-resolver-inbound',
    DomainName='cloud.com',  
    RuleType='FORWARD',
    Name='subnet2-resolver-inbound',
    TargetIps=[
        {
            'Ip': 'ip-address-of-destination',  # Replace with the actual IP address
            'Port': 53
        }
    ],
    ResolverEndpointId='resolver-endpoint-id-of-subnet2'
)


# Create the security group for the Route53 resolver outbound endpoint
resolver_outbound_sg = ec2.create_security_group(
    GroupName='route53-resolver-outbound-sg',
    Description='Security group for Route 53 resolver outbound endpoint',
    VpcId=vpc.id
)

# Authorize DNS traffic to 192.168.0.0/16
resolver_outbound_sg.authorize_egress(
    IpPermissions=[
        {
            'IpProtocol': 'udp',
            'FromPort': 53,
            'ToPort': 53,
            'IpRanges': [{'CidrIp': '192.168.0.0/16'}]
        }
    ]
)




#create route53 resolver outbound endpoint in private subnet-1
route53_resolver_outbound_1 = boto3.client('route53resolver')
route53_resolver.create_resolver_endpoint(CreatorRequestId='27-02-2024',
                                          SecurityGroupIds=[
                                                              'resolversg_out.id',
                                                            ],
                                          Direction='OUTBOUND',
                                          IpAddresses=[
                                                          {
                                                               'SubnetId': 'subnet_private_1',
                                                           },
                                                       ], )


#create route53 resolver outbound endpoint in private subnet-2
route53_resolver_outbound_2 = boto3.client('route53resolver')
route53_resolver.create_resolver_endpoint(CreatorRequestId='27-02-2024',
                                          SecurityGroupIds=[
                                                              'resolversg_out.id',
                                                            ],
                                          Direction='OUTBOUND',
                                          IpAddresses=[
                                                          {
                                                               'SubnetId': 'subnet_private_2',
                                                           },
                                                       ], )











response_outbound_subnet1 = route53.create_resolver_rule(
    CreatorRequestId='subnet1-resolver-outbound',
    DomainName='cloud.com',  
    RuleType='FORWARD',
    Name='subnet1-resolver-outbound',
    TargetIps=[
        {
            'Ip': 'ip-address-of-destination',  # Replace with the actual IP address
            'Port': 53
        }
    ],
    ResolverEndpointId='resolver-endpoint-id-of-subnet1'
)

# Create the Route53 resolver outbound endpoint for the second private subnet
response_outbound_subnet2 = route53.create_resolver_rule(
    CreatorRequestId='subnet2-resolver-outbound',
    DomainName='cloud.com',  
    RuleType='FORWARD',
    Name='subnet2-resolver-outbound',
    TargetIps=[
        {
            'Ip': 'ip-address-of-destination',  # Replace with the actual IP address
            'Port': 53
        }
    ],
    ResolverEndpointId='resolver-endpoint-id-of-subnet2'
)