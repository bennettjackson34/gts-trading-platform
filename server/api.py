import time
from flask import Flask, request
import blpapi
import json
import datetime
import sys
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_socketio import send, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app)

global session

subscriptions = blpapi.SubscriptionList()

sessionOptions = blpapi.SessionOptions()
sessionOptions.setServerHost('localhost')
sessionOptions.setServerPort(8194)


session = blpapi.Session(sessionOptions)
session.start()
session.openService("//blp/refdata")
session.openService("//blp/mktdata")

refDataService = session.getService("//blp/refdata")
mktDataService = session.getService("//blp/mktdata")


BAR_DATA = blpapi.Name("barData")
BAR_TICK_DATA = blpapi.Name("barTickData")
MKT_DATA = blpapi.Name("MarketDataEvents")
OPEN = blpapi.Name("open")
HIGH = blpapi.Name("high")
LOW = blpapi.Name("low")
CLOSE = blpapi.Name("close")
VOLUME = blpapi.Name("volume")
NUM_EVENTS = blpapi.Name("numEvents")
TIME = blpapi.Name("time")
RESPONSE_ERROR = blpapi.Name("responseError")
SESSION_TERMINATED = blpapi.Name("SessionTerminated")
CATEGORY = blpapi.Name("category")
MESSAGE = blpapi.Name("message")
SECURITIES = ["USYC5Y30 Index"]

class SubscriptionEventHandler(object):
    def getTimeStamp(self):
        return time.strftime("%Y/%m/%d %X")

    def processSubscriptionStatus(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            topic = msg.correlationId().value()
            print(f"{timeStamp}: {topic}")
            print(msg)
            if msg.messageType() == blpapi.Names.SUBSCRIPTION_FAILURE:
                print(f"Subscription for {topic} failed")
            elif msg.messageType() == blpapi.Names.SUBSCRIPTION_TERMINATED:
                # Subscription can be terminated if the session identity
                # is revoked.
                print(f"Subscription for {topic} TERMINATED")

    def processSubscriptionDataEvent(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            topic = msg.correlationId().value()
            print(f"{timeStamp}: {topic}")
            print(msg)

    def processMiscEvents(self, event):
        for msg in event:
            if msg.messageType() == blpapi.Names.SLOW_CONSUMER_WARNING:
                print(
                    f"{blpapi.Names.SLOW_CONSUMER_WARNING} - The event queue is "
                    + "beginning to approach its maximum capacity and "
                    + "the application is not processing the data fast "
                    + "enough. This could lead to ticks being dropped"
                    + " (DataLoss).\n"
                )
            elif (
                msg.messageType() == blpapi.Names.SLOW_CONSUMER_WARNING_CLEARED
            ):
                print(
                    f"{blpapi.Names.SLOW_CONSUMER_WARNING_CLEARED} - the event "
                    + "queue has shrunk enough that there is no "
                    + "longer any immediate danger of overflowing the "
                    + "queue. If any precautionary actions were taken "
                    + "when SlowConsumerWarning message was delivered, "
                    + "it is now safe to continue as normal.\n"
                )
            elif msg.messageType() == blpapi.Names.DATA_LOSS:
                print(msg)
                topic = msg.correlationId().value()
                print(
                    f"{blpapi.Names.DATA_LOSS} - The application is too slow to "
                    + "process events and the event queue is overflowing. "
                    + f"Data is lost for topic {topic}.\n"
                )
            elif event.eventType() == blpapi.Event.SESSION_STATUS:
                # SESSION_STATUS events can happen at any time and
                # should be handled as the session can be terminated,
                # e.g. session identity can be revoked at a later
                # time, which terminates the session.
                if msg.messageType() == blpapi.Names.SESSION_TERMINATED:
                    print("Session terminated")
                    return

    def processEvent(self, event, _session):
        try:
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                self.processSubscriptionDataEvent(event)
            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                self.processSubscriptionStatus(event)
            else:
                self.processMiscEvents(event)
        except blpapi.Exception as exception:
            print(f"Failed to process event {event}: {exception}")
        return False
    
def processHistoricalMessage(msg):
    security_data = msg.getElement("securityData")
    data = security_data.getElement('fieldData')

    ohlc = {"security":  security_data.getElementAsString("security"),
            "data": []}


    for bar in data.values():
        ohlc_point = {}
        x = datetime.datetime.combine(bar.getElementAsDatetime(
            "date") - datetime.timedelta(days=1), datetime.time(19, 00)).timestamp() * 1000

        # populate ohlc bar
        ohlc_point['x'] = x

        ohlc_point['close'] = bar.getElementAsFloat("PX_LAST")

        if bar.hasElement("Open"):
            ohlc_point['open'] = bar.getElementAsFloat("Open")
        else:
            ohlc_point['open'] = bar.getElementAsFloat("PX_LAST")

        if bar.hasElement("High"):
            ohlc_point['high'] = bar.getElementAsFloat("High")
        else:
            ohlc_point['high'] = bar.getElementAsFloat("PX_LAST")

        if bar.hasElement("Low"):
            ohlc_point['low'] = bar.getElementAsFloat("Low")
        else:
            ohlc_point['low'] = bar.getElementAsFloat("PX_LAST")

        ohlc['data'].append(ohlc_point)

    return (ohlc)


def printErrorInfo(leadingStr, errorInfo):
    print("%s%s (%s)" % (leadingStr, errorInfo.getElementAsString(CATEGORY),
                         errorInfo.getElementAsString(MESSAGE)))

def getPreviousTradingDate(n):
    # retrieve last traded day from N days ago
    tradedOn = datetime.date.today() - datetime.timedelta(days=n)

    while True:
        try:
            tradedOn -= datetime.timedelta(days=1)
        except OverflowError:
            return None

        if tradedOn.weekday() not in [5, 6]:
            return tradedOn


def processResponseEvent(event, processor):
    for msg in event:
        if msg.hasElement(RESPONSE_ERROR):
            printErrorInfo("REQUEST FAILED: ", msg.getElement(RESPONSE_ERROR))
            continue

        return (processor(msg))

def processIntradayMessage(msg):
    data = msg.getElement(BAR_DATA).getElement(BAR_TICK_DATA)

    ohlc = []

    for bar in data.values():
        ohlc_point = {}
        
        x = (bar.getElementAsDatetime(TIME).timestamp() * 1000) - 1000 * 60 * 60 * 6
        
        # print(x )
        # populate ohlc bar
        ohlc_point['x'] = x
        ohlc_point['open'] = bar.getElementAsFloat(OPEN)
        ohlc_point['high'] = bar.getElementAsFloat(HIGH)
        ohlc_point['low'] = bar.getElementAsFloat(LOW)
        ohlc_point['close'] = bar.getElementAsFloat(CLOSE)

        ohlc.append(ohlc_point)

    return(ohlc)

def history_ref(session, params):
    
    if not session_service:
        return {"event": "connection-failed"}

    refDataService = session.getService("//blp/refdata")

    request = refDataService.createRequest("HistoricalDataRequest")

    for security in params['securities']:
        request.getElement("securities").appendValue(security)

    for field in ['Open', "High", "Low", "PX_LAST"]:
        request.getElement("fields").appendValue(field)

    request.set("periodicitySelection", "DAILY")

    tradedOn = getPreviousTradingDate(365*5)


    # return {"error": tradedOn}
    if not tradedOn:
        return {"error": "unable to get previous trading date"}

    startTime = datetime.datetime.strftime(tradedOn, "%Y%m%d")
    request.set("startDate", startTime)

    endTime = datetime.datetime.strftime(datetime.date.today(), "%Y%m%d")
    request.set("endDate", endTime)

    session.sendRequest(request)

    try:
        done = False
        message = {
            'event': "historical-refdata-received",
            'data': {security: [] for security in params['securities']}
        }

        while not done:
            # nextEvent() method below is called with a timeout to let
            # the program catch Ctrl-C between arrivals of new events
            event = session.nextEvent(500)
            if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                # partial repsonse, add data
                response = processResponseEvent(
                    event, processHistoricalMessage)
                message['data'][response['security']] += response['data']
            elif event.eventType() == blpapi.Event.RESPONSE:
                # response is complete, add data and send

                response = processResponseEvent(
                    event, processHistoricalMessage)
                
                message['data'][response['security']] += response['data']

                return message
            else:
                for msg in event:
                    if event.eventType() == blpapi.Event.SESSION_STATUS:
                        if msg.messageType() == SESSION_TERMINATED:
                            return False
                        
    except Exception as e:
        # print(e)
        return {"status": 'error'}             
    
    finally:
        pass

def intraday_ref(session, params):
 
    # if not session_service:
    #     print(json.dumps({"event": "connection-failed"}))
    #     return

    request = refDataService.createRequest("IntradayBarRequest")

    for security in SECURITIES:

        request.set("security", security)
        request.set("eventType", "TRADE")
        request.set("interval", 5)

        tradedOn = getPreviousTradingDate(30)
        if not tradedOn:
            print("unable to get previous trading date")
            return

        startTime = datetime.datetime.combine(tradedOn, datetime.time(13, 30))
        request.set("startDateTime", startTime)

        endTime = datetime.datetime.utcnow()
        request.set("endDateTime", endTime)

        session.sendRequest(request)
        try:
            done = False
            data = []
            message = {
                'event': "intraday-refdata-received",
                'ticker': security,
                'data': []
            }

            while not done:
                # nextEvent() method below is called with a timeout to let
                # the program catch Ctrl-C between arrivals of new events
                event = session.nextEvent(500)
                if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    # partial repsonse, add data
                    message['data'] += processResponseEvent(
                        event, processIntradayMessage)
                elif event.eventType() == blpapi.Event.RESPONSE:
                    # response is complete, add data and send
                    message['data'] += processResponseEvent(
                        event, processIntradayMessage)
                    print(json.dumps(message))
                    sys.stdout.flush()
                    return True
                else:
                    for msg in event:
                        if event.eventType() == blpapi.Event.SESSION_STATUS:
                            if msg.messageType() == SESSION_TERMINATED:
                                return False
        finally:
            pass

def stream_data(securities):
    
    #session_service = session.openService("//blp/mktdata")

    # if not session_service:
    #     print(json.dumps({"event": "connection-failed"}))
    #     return {"event": "connection-failed"}

    global subscriptions
    subscriptions = blpapi.SubscriptionList()
    
    for security in securities:

        subscriptions.add(security,
                          "LAST_PRICE",
                          "interval=1",
                          blpapi.CorrelationId(security))

    
    session.subscribe(subscriptions)
    

    try:
        eventCount = 0
        # Process received events
        while True:
            # We provide timeout to give the chance to Ctrl+C handling:
            event = session.nextEvent(500)
            for msg in event:
                if event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS or \
                        event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
    
                    if msg.hasElement("PRICE_LAST_TIME_RT") and msg.hasElement("LAST_PRICE"):

                        data = json.dumps({'event': 'price-update',
                                          'ticker': msg.correlationIds()[0].value(),
                                          'x': msg.getElement('PRICE_LAST_TIME_RT').getValueAsString(),
                                          'last': msg.getElement("LAST_PRICE").getValueAsString()})
                        emit('market-data:update', data)
                        print(data)
                        # yield data
                    else:
                        # print(msg)
                        continue
                else:
                    print(msg)
                    # emit('market-data:update', msg)
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                eventCount += 1
                if eventCount >= 1000000:
                    break
                
    except Exception as e:
        print(e)
        session.stop()
        return({'event': "session-error"})
    finally:
        # Stop the session
        session.stop()
        emit('market-data:session-stopped',"session-stopped" )
        return(json.dumps({'event': "session-stopped"}))
        
def updateData(params):

    for i in range(len(params['tickers'])):
        ticker = params['tickers'][i]
        last = params['last'][i]
        last_date = datetime.datetime.fromtimestamp(int(last)/1000).strftime('%Y-%m-%d %H:%M:%S')
        
        request = refDataService.createRequest("IntradayBarRequest")
        request.set("security", ticker)
        request.set("eventType", "TRADE")
        request.set("interval", 15)

        startTime = last_date 
        request.set("startDateTime", startTime)

        endTime = datetime.datetime.utcnow()
        request.set("endDateTime", endTime)

        session.sendRequest(request)

        # return True

        try:
            done = False
            data = []
            message = {
                'event': "intraday-refdata-received",
                'ticker': ticker,
                'data': []
            }

            while not done:
                # nextEvent() method below is called with a timeout to let
                # the program catch Ctrl-C between arrivals of new events
                event = session.nextEvent(500)
                if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    # partial repsonse, add data
                    message['data'] += processResponseEvent(
                        event, processIntradayMessage)
                elif event.eventType() == blpapi.Event.RESPONSE:
                    # response is complete, add data and send
                    message['data'] += processResponseEvent(
                        event, processIntradayMessage)
                    return message
                else:
                    for msg in event:
                        if event.eventType() == blpapi.Event.SESSION_STATUS:
                            if msg.messageType() == SESSION_TERMINATED:
                                return False
        finally:
            pass



        # print(last_date)
        # test = blp.bdib(ticker=ticker, interval=60, fields=['open', 'high', "low", 'px_last'], dt=last_date, ref='IndexUS', session='noAsian')
        # # test = blp.bdh(ticker, ['open', 'high', "low", 'px_last'], last_date)

        # print(test)
        # return True
        #     # return data
    
@app.route("/time")
def get_time():
    return ({'status': "suck"})

@app.route("/create_session")
def create_session():
    session = blpapi.Session(sessionOptions)

    return {'status': True}

@app.route("/start_session")
def start_session():
    try:
        start = session.start()
        return {"status": start}
    except Exception as e:
        return {"status": "error"}

@app.route("/create_subscription", methods = ['GET', 'POST'])
def create_subscription():
    securities = set(request.json['securities'])
    
    print(securities)

    try:      
        return stream_data(securities), {"Content-Type": "application/x-ndjson"}
   
    except Exception as e:
        # print(e)
        return {"status": "error"}


@app.route("/get_history")
def get_history():
    securities = request.json['securities']
    # starts = request.data.get("start").split(",")
    # ends = request.data.get("end").split(",")
    # closes = request.data.get("close").split(",")
    # lasts = request.data.get("last").split(",")

    params = {'securities': securities}

    try:
        test = history_ref(session, params)
        # test = updateData(params)
        return test
        # return history_complete
    except Exception as e:
        # print(e)
        return {"status": "error"}


@app.route("/stop_session")
def stop_session():
    try:
        stop = session.stop()

        if stop:
            session.destroy()
            return {"status": stop}
    except Exception as e:
        return {"status": e}

def test(lst):
    print(lst)
    
@socketio.on('market-data:subscribe')
def handle_subscription(data):
    securities = set(data['securities'])
    
    stream_data(securities)

    return 
    
@socketio.on('market-data:unsubscribe')
def handle_unsubscribe(data):
    print('unsubscribing')
    securities = set(data['securities'])
    
    session.unsubscribe(subscriptions)
    
if __name__ == "__main__":
    socketio.run(app)
