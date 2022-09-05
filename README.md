# SAD: slack-anti-delete

TL;DR: I patched my Slack client to keep messages that others delete.

Let's say someone sent me a message, immediately regretted it and tried to delete it. They will think the message got deleted on both ends ("delete for everyone"), but using this patch my client will keep the message anyway and notify me that someone tried to delete it 😬. [This is a follow-up research I did on how Slack is working internally](https://github.com/SharonBrizinov/slack-sounds).

https://user-images.githubusercontent.com/519424/188516996-d0c73281-32de-4f20-9317-6cba84d9050c.mov

As a bonus, you'll also get a nice notification telling you who tried to delete a message.
<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188516989-223be9c4-e710-488b-9b6f-d59626abafdf.jpg">
</p>

## Instructions (Mac OSX only)
run `python3 slack_patch_delete.py`.

## Backstory
The backstory is kind of funny - not so long ago my friend had a rant about his former boss. He told me a story of how his former boss accidently sent him a nasty message and then immediately deleted it. My friend wanted to confront him but had no proof because the message was gone too quickly..

## Technical Details
After my previous research on [how Slack manages local cache media files](https://github.com/SharonBrizinov/slack-sounds/edit/main/README.md), I moved forward to research how the JS code files are stored. I opened Slack in debug mode and started to dig in. Turns out the JS files are also kept in special offline static cache files with proprietary binary format. 

The first stop is `SLACK_DIR/Code Cache/js`. (BTW on Mac OSX Slack dir can be `~/Library/Application Support/Slack` or `~/Library/Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack`).

<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188517504-b8a21bd8-40ff-4608-8b2e-2a055875f7d9.png">
</p>

These cache files contain binary formatted data of the requests and responses that Slack client is sending and receiving to/from the server. Slack devs probably wanted to create a balance between the statically offline Electron ASAR archive versus the overhead of sending online requests all the time - so they created a simple yet powerful trade-off. They are sending "live" HTTP requests but with heavy use of static cache files storing both the requests and the responses. Therefore, if a new request is fired, the request will never leave the machine; the entire loop will be closed locally offline and only static JS files will be read from the disk.

But the journey to full JS execution is longer than I thought. The JS code cache files under the `Code Cache/js` directory are binary serialized JS files and this is the first stop when receiving new JS code from the server.

<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188517731-d8b0f455-3592-4462-a2df-a94869328375.png">
</p>

Next, Slack unpacks the JS code and stores it in a different JS code cache directory under `SLACK_DIR/Service Worker/CacheStorage`
<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188517826-5c375ab9-b0eb-4ffb-bc9e-ee83ed2bbeb0.png">
</p>

Here, the JS code is unpacked and looks much like the regular obfuscated Slack code we are used to see while debugging it.
<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188517875-994bea70-fcc3-4f1d-85a9-1c24a7eaa526.png">
</p>

Cool, so now we know where the actual code is found. But what do we need to patch in order to keep deleted messages? I used Chrome debugging tools to inspect all HTTP requests and WebSocket traffic. I quickly found out that most of the action takes place through WebSocket messages. 

<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188518006-7f9de2db-51f0-46fd-853f-9f734620cd04.png">
</p>

The ongoing WebSocket session is very chatty and there are a lot of different message `subtypes`s but the most important one for us is `message_delete`.
<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188518224-da7ccf20-a2bb-4114-b6c1-7c76b9686a2a.png">
</p>

Cool. So all we need to do now is modify the JS flow so it will ignore this message type when received. We need to locate the main `switch` that handles incoming message types and modify the `message_delete` case.

<p align="center">
<img alt="image" src="https://user-images.githubusercontent.com/519424/188518385-f1e319e4-16c6-499d-b153-e24891520e75.png">
</p>

Bingo. Now we can patch the JS cache files and force our client to ignore 'delete message' requests ;)

