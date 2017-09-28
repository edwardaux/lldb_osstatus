This project provides a custom LLDB command called `osstatus` that uses the awesome [OSStatus.com](osstatus.com) service to query what various iOS/macOS/tvOS/watchOS error codes mean. 

### Usage
At its simplest, you can just pass in an error code. For example, to see what `-1009` really means:

```
(lldb) osstatus -1009
kCFURLErrorNotConnectedToInternet CFNetwork(CFNetworkErrors.h)
NSURLErrorNotConnectedToInternet  Foundation(NSURLError.h)
```

You can optionally pass a verbose flag `-v` to get more information (if available):

```
(lldb) osstatus -1009 -v
kCFURLErrorNotConnectedToInternet CFNetwork(CFNetworkErrors.h)
    The connection failed because the device is not connected to the
    internet.
NSURLErrorNotConnectedToInternet  Foundation(NSURLError.h)
    Returned when a network resource was requested, but an internet
    connection is not established and cannot be established
    automatically, either through a lack of connectivity, or by the
    user's choice not to make a network connection automatically.
```

### Installation
Download and save `osstatus.py` to your local machine (it doesn't really matter where you save it.)

Add the following to your `$HOME/.lldbinit` file (assuming you saved to your Desktop):

```
command script import ~/Desktop/osstatus.py
```

**Important: you will need to restart Xcode for the command to become available.**

### Notes
The command needs an active working internet connection in order to connect to the osstatus.com service. If your internet connection is slow, it may take several seconds for the command to return.

### Data Privacy
In an ideal world, I would love for the command to submit API requests directly from lldb to the osstatus.com API, however, due to a technical limitation in Apple's version of macOS Python (it unfortunately does not contain support for SSL SNI), it means connecting directly results in an SSL error every time.  There are a number of 3rd-party libraries (eg. requests) that solve this problem, however, there is no guarantee that users of this utility will have those libraries installed.

As a workaround, this utility connects to an AWS instance (that does not have SSL SNI enabled) that simply proxies the request directly to osstatus.com. Rest assured, I have no interested in capturing or logging the error codes that you lookup.

If you believe you can get `urllib2` working with SSL SNI, please feel free to [contact me](https://twitter.com/edwardaux). I'd love to be able to remove this intermediary service.

### License
This code is distributed under the terms and conditions of the MIT license.