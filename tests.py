import eta_classifier
import asyncio
import os

NO_ETA_TEST_CASES = \
    [
        "Will hard fork be ready by the time paper 1.21 releases?",
        "Paper does not give any estimates for 1.21, or any other releases, ever. Get it?",
        "When paper 1.21 release, will we be able to play it stably?",
        "I hate people who keep asking ''when will 1.21 paper release??''",
        "Is the paper 1.21 repo still missing some patches before release?",
        "Will paper 1.21 include the trader rebalance?",
        "Does this coincide with paper going to 1.21?",
        "Hello, since when is Paper 1.21 still marked as experimental?",
        "Did paper add additional synchronization to classloaders in 1.20.6/1.21? I've noticed that the main thread seems to hang while classes are being loaded",
        "I don't care when paper 1.21 will release",
        "Are there any major API changes expected in Paper 1.21?",
        "How does Paper 1.21 compare to other server software in terms of performance?",
        "Will Paper 1.21 support the new biomes introduced in the vanilla update?",
        "Has anyone successfully migrated their plugins to work with Paper 1.21 yet?",
        "What new features are you most excited about in Paper 1.21 when it releases?",
        "Is Paper 1.21 compatible with older world saves?",
        "How does the memory usage of Paper 1.21 compare to previous versions?",
        "Are there any known issues with chunk loading in Paper 1.21?",
        "Will Paper 1.21 require a different Java version than previous releases?",
        "Has the community started developing custom plugins specifically for Paper 1.21?",
        "yo any1 kno if papr 1.21 gonna hav bettr mob AI?",
        "pls tell me paeper 1.21 fixes da chunk issues!!1!",
        "wuts da biggest change in Paper 1.21 release? im curious lol",
        "can sum1 explain y Paper 1.21 is takin so long 2 develop and release?",
        "r der gonna b new cmds in Papr 1.21? pls say yes!",
        "Paper 1.21 betta fix da lag or imma rage quit fr fr",
        "ppl keep talkin bout Paper 1.21 but idk wut it even is tbh",
        "omg pls tell me 1.21 Paper will work w/ my fav plugins!!",
        "y is every1 so hyped 4 Paper 1.21? wuts da big deal?",
        "dat feel when u wait 4 Paper 1.21 but it still aint here smh",
        "Hey everyone! I've been working on estimating server performance improvements, and I'm wondering if Paper 1.21 will include any new metrics for this kind of analysis?",
        "As a longtime Minecraft server admin, I've seen many releases come and go. I'm curious about what new features Paper 1.21 might bring to the table, especially in terms of plugin compatibility.",
        "In my experience, the timeframe between major updates can vary widely. With that in mind, what kind of changes to world generation can we expect in Paper 1.21?",
        "I remember the date when I first started using Paper, and it's been a wild ride since then! For Paper 1.21, are there any plans to improve the built-in profiling tools?",
        "Given the recent changes to mob spawning mechanics, I'm trying to estimate how this might affect my farm designs. Will Paper 1.21 include any specific optimizations for mob spawning?",
        "Hey folks! I'm planning a server event, and while I know better than to ask for release dates, I'm wondering if Paper 1.21 will include any new features for server-wide announcements or events?",
        "As someone who likes to keep a close eye on development timeframes, I've noticed that Paper 1.21 seems to be a significant update. Are there any particular areas of focus for this version?",
        "I've been working on estimating the impact of various server configurations on performance. Does anyone know if Paper 1.21 will introduce any new configuration options that might affect these estimates?",
        "With every new release, I enjoy diving into the changelogs. For Paper 1.21, are there any plans to change how these logs are structured or presented?",
        "In my calendar, I always mark the dates of major Minecraft updates. While we wait for Paper 1.21, has anyone heard about potential changes to how Paper handles chunk loading or unloading?",
        "uyafsafsauyfs??? paper ??? 1.21 releasded dateeee westimate pls hivoagoogos"
]

ETA_TEST_CASES = \
    [
        "Any idea when Paper 1.21 might drop? Been waiting forever!",
        "Do we have even a rough timeline for the Paper 1.21 release? Just curious.",
        "Has the dev team hinted at a possible release window for Paper 1.21?",
        "I'm planning a server upgrade. Should I wait for Paper 1.21 or is it still months away?",
        "Paper 1.21 when??? The suspense is killing me!",
        "Are we looking at weeks or months for the Paper 1.21 release at this point?",
        "Has anyone heard whispers about a target date for Paper 1.21?",
        "Just wondering if Paper 1.21 is on track for a Q3 release or if it's slipped?",
        "Can someone from the Paper team give us a ballpark ETA for 1.21? Even just the month would be helpful!",
        "Is Paper 1.21 likely to be out before the holidays, or should I not get my hopes up?",
        "Is there any rough eta for 1.21 for paper or nah?",
        "hello everyone pls when will 1.21 paper release?",
        "Hey Paper community! I've been closely following the development progress and I'm really excited about the upcoming features. I know it's a complex process, but does anyone have an estimate on when we might see Paper 1.21 released?",
        "As a server admin planning for future updates, I'm trying to coordinate some changes with my team. To help with our scheduling, could someone provide a rough timeframe for when Paper 1.21 might be available?",
        "I've been working on a major plugin update that I want to coincide with Paper 1.21. To assist with my development timeline, is there any information available about the expected release date for this version?",
        "Long-time Paper user here! I'm amazed at how far we've come since I first started. Speaking of progress, I'm curious if there's any word on when we might expect to see Paper 1.21 drop? Even a ballpark estimate would be helpful for planning purposes.",
        "Hey folks! I'm organizing a big server event and I'm hoping to showcase some new features from Paper 1.21. To help with my event planning, does anyone have insight into when this version might be released?",
        "I've been eagerly anticipating Paper 1.21 and all the improvements it'll bring. I know software development can be unpredictable, but has there been any indication of a potential release window for this version?",
        "As someone who likes to stay on top of the latest Minecraft tech, I'm really looking forward to Paper 1.21. To satisfy my curiosity, has the team shared any estimates on when we might see this version hit the servers?",
        "I'm in the process of upgrading my server infrastructure and I'm hoping to time it with the release of Paper 1.21. To help with my upgrade schedule, is there any information available about when this version might be ready?",
        "Hello Paper devs and community! I'm working on a YouTube series about Minecraft server technology, and I'd love to feature Paper 1.21. To help with my content planning, do you have any rough idea when this version might be released?",
        "I've been following the development of Paper 1.21 with great interest. As I'm planning some major changes to my server, it would be really helpful to know if there's any estimated timeframe for when this version might be available. Any insights?"
    ]

async def check_classification_correct(*, classifier: eta_classifier.EtaClassifier, query: str, belongs_to_class: bool) -> bool:
    classification = await classifier.classify(query)
    if classification.belongs_to_class == belongs_to_class:
        print(f"Correct classification for query {query}")
        return True
    else:
        print(f"Incorrect classification for query {query}.\nClass correspondence fail reason: {classification.fail_reason}")
        return False

async def test():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    classifier = await eta_classifier.EtaClassifier.with_openai(
        api_key=api_key, 
        model="gpt-3.5-turbo"
    )

    false_positives, false_negatives = 0, 0
    total = len(ETA_TEST_CASES) + len(NO_ETA_TEST_CASES)

    for no_eta_case in NO_ETA_TEST_CASES:
        if not await check_classification_correct(classifier=classifier, query=no_eta_case, belongs_to_class=False):
            false_positives += 1
            
    for eta_case in ETA_TEST_CASES:
        if not await check_classification_correct(classifier=classifier, query=eta_case, belongs_to_class=True):
            false_negatives += 1

    print(f"Total tests: {total}. False positives: {false_positives}. False negatives: {false_negatives}.")

asyncio.run(test())

