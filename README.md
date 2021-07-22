# trbo-data-svc

This is a collection of multiple different libraries and programs that interface with MotoTRBO digital radios.

Currently supported:

- ARS
- TMS

In the works:

- LRRP
- Job Tickets
- Impres OTA Battery Management (low priority, weird format)

## Basic Layout

Most of the basic data services can be set up as such:

    from TrboDataSvc import ars
    def callback(rid, data):
        print("Got a message from radio id {}".format(rid))
        return True
    listener = ars.ARS()
    listener.register_callback(callback)
    listener.listen()

That's all you need!

## Further Documentation

### The callbacks

The callback function definition should be in the following format:

    def callback_name(rid, data)

Obviously the name can be whatever you want, but the arguments must be rid and data, in that order. The type of `data` and what it passes will differ between the different functions. It can be either an int, string, or dictionary.

Additionally, the callback must return True on successful processing and False on unsuccessful processing. Returning true means an ACK gets sent to the radio when necessary. Examples of failed processing might be an exception, upstream server offline, etc.

### Listen function

The listen function creates a separate process to process the incoming data. This creates a new Process for each listener. This shouldn't be a huge deal but on embedded systems it might be something to consider as a new Process creates an entirely new memory space.

## Other tools

The `util` class offers a few utilities such as `id2ip` and `ip2id` that convert the OTA IP to a radio ID. In case you are not familiar, the DMR radio ID gets mapped to an IP address for data transmission over the air. These functions let you easily convert between OTA IPs and RIDs.
