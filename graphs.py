import boto3
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from yaml import load
from dateutil.parser import parse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--start', type=parse, required=True)
    parser.add_argument('--end', type=parse, required=True)
    parser.add_argument('--graph', type=argparse.FileType('r'), required=True)

    args = parser.parse_args()

    config = load(args.graph)

    for name, graph in config['graphs'].items():

        cloudwatch = boto3.resource('cloudwatch', region_name=graph['region'])
        metric = cloudwatch.Metric(graph['namespace'], graph['metric'])

        data = {}

        for dimension in graph['dimensions']:
            dimensions = [
                {
                    'Name': dimension['name'],
                    'Value': dimension['value'],
                },
            ]

            if 'region' in dimension:

                dimensions.append({
                    'Name': 'Region',
                    'Value': dimension['region'],
                })

            response = metric.get_statistics(
                Dimensions=dimensions,
                StartTime=args.start,
                EndTime=args.end,
                Period=graph['period'],
                Statistics=graph['statistics'],
            )

            datapoints = response['Datapoints']

            data[':'.join((dimension['name'], dimension['value']))] = \
                [d[graph['statistics'][0]] * graph.get('multiplier', 1)
                 for d in datapoints]

        df = pd.DataFrame(data, index=[d['Timestamp'] for d in datapoints])

        s = 0
        for column, series in df.items():
            s += series.sum()

        title = graph.get('title', '').format(sum=s)
        df.plot(grid=True, title=title, figsize=(10, 6), style='.-')
        plt.ylim(ymin=0)
        plt.ticklabel_format(useOffset=False, style='plain', axis='y')
        plt.savefig('{}.png'.format(name))


if __name__ == '__main__':
    main()
