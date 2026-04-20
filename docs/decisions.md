## This File contians all kind  of decisions.

### 1. Default zyclic node/topic-frequency
The Node Frequency and the corresponding publishing frequency should be 10Hz by default. Therefore the messages should be published ever 0.1s even if the content may be empty.  
If the Frequency should be different in some nodes or topics this is has to be documented especially.  
The reason for the 10Hz as a default value is the estimated sweetspot between speed and performance.

### 2. Position as List instead of Tuple
In the development process, the initial idea was to store the position as a tuple. However, for the postion prediction we changed our implementation to use a list instead. This is beneficial because the x-coordinate can be modified more easily, since lists are mutable while tuples are not.