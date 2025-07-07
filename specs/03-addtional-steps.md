a) install and configure monitoring of all the nodes (master and worker)
use grafana and prometheus to show the cluster stats (cpu/mem/disk i-o/gpu and network ) include all metrics which are crucial to find bottlenecks in the cluster across all nodes.

b) break the final ansible scripts into individual chunks based on each checkpoint
allowing the human in the loop, if approval is needed to cleanup old install or 
having to install docker or ansible or any other components. In a nutshell any big activity which might affect an existing configured ray cluster. we will eventually call REST API's using a WebUI to call all these scripts. ultrathink and design the system appropriately, to cover for these design requirements.