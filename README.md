# TCP Over UDP

Selective repeat is used for flow control. For congestion control the code 
increases the ```cwnd``` exponentially up to ```ssthresh``` and in case of 3 duplicate
ACKs the ```cwnd``` and ```ssthresh``` are reset.


#### Note
I still have doubt in implementations, any help or PR is appreciated.
