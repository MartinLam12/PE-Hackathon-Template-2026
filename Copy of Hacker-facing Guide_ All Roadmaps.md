# PE Challenge: Getting Started Guide

> **Internal Note for Reviewers:** The verification criteria listed under each tier are examples of what judges may look for/what is expected by automated validation scripts, not finalized requirements. **Specific judging expectations are subject to change as the event structure is finalized.**

---

## How This Event Works

You and your team start with a *pre-built URL shortener application* and compete to earn achievements by following **Production Engineering Roadmaps**. Each roadmap represents a core PE discipline, with three progressive tiers (Bronze \-\> Silver \-\> Gold) that build on each other. You can go deep on one roadmap or mix and match across several \- but we recommend starting with one and completing it in order.

Below is a brief overview of what each roadmap covers. Read through these descriptions to figure out which path suits your team best, then jump into the full guide for your chosen roadmap.

---

## Choose Your Path

[**Reliability Engineering**](#getting-started:-reliability-engineering) \- Build confidence that your service actually works. You’ll write automated tests, measure coverage, and eventually break your own service on purpose to prove it can recover. *Best for teams interested in testing, service health, and building trust in deployments.*

[**Scalability Engineering**](#getting-started:-scalability-engineering) \- Make your service handle real-world load. You’ll run load tests, scale horizontally with multiple instances, and optimize performance with caching. *Best for teams interested in performance and understanding system limits.*

[**Incident Response**](#getting-started:-incident-response) \- Know when things break and respond quickly. You’ll implement structured logging, set up alerting, and build dashboards that give you real-time visibility into your service. *Best for teams interested in monitoring, alerting, and operational readiness.*

[**Documentation (Bonus)**](#getting-started:-documentation-\(bonus\)) \- This standalone bonus category rewards teams who invest in operational documentation \- the kind of work that Production Engineers do every day but rarely gets attention or consideration. *Can be pursued alongside any roadmap for extra points.*

---

---

# Getting Started: Reliability Engineering {#getting-started:-reliability-engineering}

## What Is This Roadmap About?

In the real world, Production Engineers don’t just write code \- they make sure that code *keeps working*. Reliability Engineering is about building confidence that your service does what it’s supposed to do, handles unexpected input gracefully, and recovers when things go wrong.

This roadmap takes you from writing your first automated tests all the way to intentionally breaking your service to prove it can recover. If you’ve never written a test before, Bronze is designed to get you started. If you already test your code, Silver and Gold will push you into territory that mirrors what PE teams do at companies like Meta every day\!

**You’ll walk away understanding:** Why automated testing matters for production systems, how to measure test coverage, and how to think about failure as something you *plan for* rather than something that just happens to you.

---

## The Tiers at a Glance

**Bronze: “Tested” (10 pts)** \-\> Write automated tests, run them in CI, add a health check endpoint.

**Silver: “Coverage” (25 pts)** \-\> Hit 50%+ test coverage, add integration tests, block bad deploys with failing tests.

**Gold: “Reliability Proven” (50 pts)** \-\> Reach 70%+ coverage, handle errors gracefully, and run basic chaos/failure tests.

Each tier builds on the one before it. We recommend completing them in order.

---

## Bronze: “Tested”

### What You Need to Do

- Write an automated test suite (unit tests at minimum)  
- Have those tests run automatically in your CI pipeline on every commit  
- Add a health check endpoint that returns your service’s status (for example, GET /health returns 200 OK)

### Key Concepts

**Unit tests** check that individual pieces of your code work correctly in isolation. For example, if your URL shortener has a function that generates a short code from a long URL, a unit test would call that function with a known input and verify the output is what you expect. You’re not testing the whole app end-to-end \- you’re testing one small piece at a time.

**A health check endpoint** is a simple route (usually /health or /status) that returns a quick response confirming the service is running. Monitoring tools, load balancers, and CI pipelines use health checks to know if your app is alive. It doesn’t need to be fancy \- returning a status of “ok” with a 200 status code is enough for Bronze.

### Recommended Tools

The tools listed below are suggestions based on what works well with the project template stack. You’re welcome to use alternatives that accomplish the same goals.

- **pytest** \- The standard Python testing framework. Simple, widely used, and works with Flask out of the box.  
- **GitHub Actions** (or similar CI tool) \- For running your tests automatically on every commit.

### Verification (Examples)

- A test suite that runs successfully (test output or CI logs showing tests passing)  
- A CI pipeline config that runs tests on commits  
- A working health check endpoint

### Resources

- [Flask Official Testing Guide](https://flask.palletsprojects.com/en/stable/testing/) \- How to set up a test client and write tests for Flask apps  
- [TestDriven.io: Testing Flask with Pytest](https://testdriven.io/blog/flask-pytest/) \- Practical walkthrough covering fixtures, unit tests, and functional tests  
- [GitHub Actions Quickstart](https://docs.github.com/en/actions/quickstart) \- Setting up a basic CI pipeline

---

## Silver: “Coverage”

### What You Need to Do

- Achieve 50%+ test coverage (or equivalent meaningful coverage)  
- Write integration tests in addition to unit tests  
- Configure your CI pipeline so that failing tests block deployment  
- Document your basic error handling approach

### Key Concepts

**Test coverage** measures what percentage of your code actually gets executed when your tests run. If you have 100 lines of code and your tests exercise 60 of them, you have 60% coverage. It’s not a perfect measure of quality \- you could have 100% coverage with bad tests \- but it’s a useful signal for identifying untested code paths. The number and quality of tests will be considered, so try to test real behavior\!

**Integration tests** differ from unit tests in scope. While unit tests check one function or method in isolation, integration tests check that multiple parts of your system work together. For example, “when I POST a URL to /shorten, does it store in the database AND return a valid short link?” For Silver, you need both types. A good approach: start by writing unit tests for your core logic, then write integration tests that hit your API endpoints and verify the full request-response cycle.

**Blocking deployment on test failure** means configuring your CI pipeline so that if any test fails, the code doesn’t get deployed. This is a fundamental PE practice \- never ship code that breaks existing tests.

### Recommended Tools

- **pytest-cov** \- A pytest plugin that adds coverage reporting. It wraps the coverage.py library and gives you a report showing which lines are and aren’t covered.

### Verification (Examples)

- A coverage report showing 50%+  
- Evidence of both unit and integration tests in your test suite  
- A CI configuration where failing tests prevent deployment  
- Some documentation of how your app handles errors (can be a section in your README)

### Resources

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/) \- Reference for the coverage plugin, including report formats  
- [Flask Tutorial: Test Coverage](https://flask.palletsprojects.com/en/stable/tutorial/tests/) \- Official Flask tutorial section on measuring coverage  
- [GitHub Actions: Creating Dependent Jobs](https://docs.github.com/en/actions/using-workflows/about-workflows#creating-dependent-jobs) \- Making deployment depend on tests passing

---

## Gold: “Reliability Proven”

### What You Need to Do

- Reach 70%+ test coverage with meaningful tests  
- Your service recovers gracefully from errors (doesn’t crash on bad input)  
- Run basic chaos/failure testing (kill a process, show recovery)  
- Document your known failure modes and expected behavior

### Key Concepts

**Chaos/failure testing** is the practice of intentionally introducing failures to see how your system responds. The idea is that if you wait for failures to happen naturally, they’ll happen at the worst possible time. Instead, you cause them on purpose so you can observe, learn, and build resilience proactively.

For this hackathon, you don’t need a full chaos engineering platform. Simple approaches count: kill your app process and show it restarts, send malformed requests and show proper error responses instead of crashes, simulate a database connection failure and show your app handles it, or temporarily take down a dependency and show the service degrades rather than dying.

**Graceful error handling** means your service doesn’t crash or return a raw stack trace when something goes wrong. Instead, it returns a meaningful error response \- a missing resource returns 404 with a clear message, a malformed request returns 400 with an explanation, a database timeout returns 503 instead of crashing the whole process.

**Failure mode documentation** is exactly what Production Engineers write in runbooks at real companies. It describes what can go wrong with your service, what your service does when each failure happens, and how you tested each scenario. This is how on-call teams know what to do at 3am when something breaks.

### Verification (Examples)

- Coverage report showing 70%+ with tests that check meaningful behavior  
- A demo of your app handling bad input without crashing  
- A demo of inducing a failure and showing recovery  
- Documentation of failure modes and expected behavior

### Resources

- [Principles of Chaos Engineering](https://principlesofchaos.org/) \- The foundational document on why and how to do chaos testing  
- [Flask Error Handling](https://flask.palletsprojects.com/en/stable/errorhandling/) \- Registering custom error handlers in Flask  
- [Docker Restart Policies](https://docs.docker.com/engine/containers/start-containers-automatically/) \- Configuring containers to restart after failures  
- [Awesome Chaos Engineering (GitHub)](https://github.com/dastergon/awesome-chaos-engineering) \- Curated list of chaos engineering resources and tools

---

## Tips for Your Team

- **Start with Bronze early.** Get your tests running in CI before you try anything ambitious. A working pipeline you can iterate on is more valuable than a perfect plan.  
- **Split the work.** One teammate can focus on writing tests while another sets up CI and the health check endpoint. Gold-level chaos testing can be a separate workstream.  
- **Don’t chase coverage for coverage’s sake.** Write tests that would actually catch a bug \- not tests that just pad the number.  
- **Document as you go.** Gold requires failure mode documentation. It’s easier to write while you’re building than to reconstruct at the end.  
- **Keep it simple.** Killing a Docker container and showing it restarts is a perfectly valid chaos test for this event.

---

---

# Getting Started: Scalability Engineering {#getting-started:-scalability-engineering}

## What Is This Roadmap About?

At some point, every successful service has to answer the question: “What happens when more people start using this?” Scalability Engineering is about understanding your service’s limits, proving it can handle real-world load, and making it faster and more resilient as traffic grows.

This roadmap takes you from running your first load test all the way to optimizing performance with caching and running multiple instances behind a load balancer. If you’ve never thought about how many users your app can handle, Bronze will open your eyes. If you already know your app is slow, Silver and Gold give you the tools to fix it.

**You’ll walk away understanding:** How to measure your service’s performance under load, what horizontal scaling means in practice, and how caching and optimization keep real-world services responsive.

**Note:** Load testing and running multiple instances may require adequate system resources. Plan accordingly and keep an eye on your machine’s capacity.

---

## The Tiers at a Glance *(acceptance criteria open to change)*

**Bronze: “Load Tested” (10 pts)** \-\> Configure a load testing tool, handle 50+ concurrent users, and document baseline performance.

**Silver: “Scaled” (25 pts)** \-\> Run multiple instances, add a load balancer, and handle 200+ concurrent users.

**Gold: “Performance Optimized” (50 pts)** \-\> Implement caching, identify and fix bottlenecks, and handle 500+ concurrent users.

Each tier builds on the one before it. We recommend completing them in order.

---

## Bronze: “Load Tested”

### What You Need to Do

- Configure a load testing tool (k6, Locust, JMeter, or similar)  
- Demonstrate your service handles 50+ concurrent users without errors  
- Document basic performance metrics (response time, error rate)

### Key Concepts

**Load testing** is the practice of simulating many users hitting your service at the same time to see how it behaves under stress. Instead of clicking around in your browser and hoping for the best, you use a tool to send hundreds or thousands of requests automatically and measure what happens. Does the response time stay acceptable? Do requests start failing? Does the service crash entirely?

**Concurrent users** means the number of simulated users making requests at the same time. When you say your service “handles 50 concurrent users,” you’re saying that 50 users can simultaneously interact with your service and all get successful responses within a reasonable time.

**Performance metrics** are the numbers you collect during a load test. The most important ones for this roadmap are response time (how long it takes to get a response \- usually measured as average and p95, which is the time within which 95% of requests complete) and error rate (what percentage of requests fail). These give you a baseline picture of how your service performs.

### Recommended Tools

The tools listed below are suggestions based on what works well with the project template stack. You’re welcome to use alternatives that accomplish the same goals.

- **k6** \- A modern, developer-friendly load testing tool. Tests are written in JavaScript and run from the command line. Lightweight and easy to get started with.  
- **Locust** \- A Python-based load testing tool with a web UI. Good choice if your team is more comfortable staying in the Python ecosystem.

### Verification (Examples)

- Load test results showing 50+ concurrent users handled  
- Performance metrics documented (response time, error rate)  
- Load test script or configuration in your repository

### Resources

- [k6 Documentation](https://k6.io/docs/) \- Comprehensive guide to writing and running load tests with k6  
- [k6 Getting Started Tutorial](https://grafana.com/docs/k6/latest/examples/get-started-with-k6/) \- Hands-on intro to writing your first k6 test  
- [Locust Quickstart](https://docs.locust.io/en/stable/quickstart.html) \- Getting started with Python-based load testing

---

## Silver: “Scaled”

### What You Need to Do

- Demonstrate your service handles 200+ concurrent users  
- Run multiple instances of your service (2+ containers/servers)  
- Set up a load balancer or reverse proxy to distribute traffic  
- Achieve response times under 3 seconds (or some small difference from baseline) under load

### Key Concepts

**Horizontal scaling** means running multiple copies (instances) of your service to handle more traffic. Instead of making one server faster (vertical scaling), you add more servers and spread the work across them. This is how most large-scale web services work \- if one instance gets overwhelmed, you spin up more.

**A load balancer** sits in front of your service instances and distributes incoming requests across them. When a user makes a request, the load balancer decides which instance should handle it. This prevents any single instance from being overwhelmed and means you can add or remove instances as demand changes. Nginx is a popular choice that can act as both a web server and a load balancer.

**A reverse proxy** is a server that sits between clients and your application servers. It receives requests from the internet and forwards them to the appropriate backend service. Nginx is one of the most common reverse proxy for web applications. In practice, your Nginx setup will often act as both a reverse proxy and a load balancer \- accepting traffic from the outside and distributing it to your Flask instances.

For this tier, a practical setup is: multiple Flask containers running behind an Nginx reverse proxy, all orchestrated with Docker Compose.

### Recommended Tools

- **Nginx** \- Industry-standard reverse proxy and load balancer. Highly performant and well-documented.  
- **Docker Compose** \- Scale your service by defining multiple container replicas in your compose file.

### Verification (Examples)

- Load test results showing 200+ concurrent users with acceptable response times  
- Evidence of multiple instances running (like docker ps showing 2+ containers)  
- Load balancer or reverse proxy configuration in your repository  
- An explanation of your scaling approach

### Resources

- [Nginx Load Balancing Guide](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) \- Configuring Nginx to distribute traffic across multiple servers  
- [Flask Deployment with Nginx (Official Docs)](https://flask.palletsprojects.com/en/stable/deploying/nginx/) \- Setting up Nginx as a reverse proxy for Flask  
- [Docker Compose: Scaling Services](https://docs.docker.com/compose/how-tos/scaling/) \- Running multiple instances of a service with Docker Compose  
- [TestDriven.io: Dockerizing Flask with Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/) \- End-to-end walkthrough of Flask \+ Gunicorn \+ Nginx in Docker

---

## Gold: “Production Ready”

### What You Need to Do

- Demonstrate your service handles 500+ concurrent users OR 100+ requests/second  
- Implement caching (Redis, in-memory, CDN, etc.)  
- Identify and address at least one performance bottleneck  
- Maintain a reasonable error rate (for example, under 5% at peak load)

### Key Concepts

**Caching** is storing the results of expensive operations so you don’t have to repeat them. If your URL shortener looks up the same short code in the database thousands of times, a cache can store that result in memory so subsequent lookups are nearly instant. Redis is the most popular caching solution for web applications \- it’s an in-memory data store that’s extremely fast and straightforward to integrate with Python.

**Identifying bottlenecks** means figuring out which part of your system is the limiting factor under load. Is it the database? The application code? Network latency? You find bottlenecks by analyzing your load test results \- look for where response times spike, where errors start appearing, or where resource usage (CPU, memory) maxes out. Once you find the bottleneck, you can address it through caching, query optimization, connection pooling, or other techniques.

**Connection pooling** is a technique where your application maintains a pool of reusable database connections instead of opening a new connection for every request. Opening a database connection is relatively expensive, so reusing them significantly improves performance under load. Most Python database libraries support this.

### Verification (Examples)

- Load test results showing 500+ concurrent users or 100+ requests/second  
- Evidence of caching in action (for example, cache hit rates, before/after response times)  
- An explanation of the bottleneck you identified and how you addressed it  
- Error rate metrics showing stability under peak load

### Resources

- [Redis Quickstart](https://redis.io/docs/latest/get-started/) \- Getting started with Redis for caching  
- [Flask-Caching Documentation](https://flask-caching.readthedocs.io/) \- Adding caching to Flask applications with support for Redis and other backends  
- [k6: Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) \- Setting pass/fail criteria for your load tests (for example, p95 response time, error rate)  
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html) \- Configuring database connection pools in Python

---

## Tips for Your Team

- **Establish a baseline first.** Run a load test before you change anything. You need to know how your unmodified service performs so you can measure improvement.  
- **Split the work.** One teammate can write load test scripts while another sets up Nginx and Docker Compose scaling. Caching can be a separate workstream for Gold.  
- **Watch your machine’s resources.** Load testing and running multiple containers can be demanding. Keep an eye on your CPU and memory \- if your test machine is maxed out, the results won’t be meaningful.  
- **Small changes, big impact.** Adding a cache for your most-hit endpoint or adding a second instance behind Nginx can dramatically improve throughput. Start with the obvious wins.  
- **Document your numbers.** Judges want to see before-and-after metrics. Screenshot your load test results at each stage.

---

---

# Getting Started: Incident Response {#getting-started:-incident-response}

## What Is This Roadmap About?

In production, things break. The question isn’t whether your service will have problems \- it’s how quickly you’ll *know* about them and how effectively you’ll respond. Incident Response is about building the visibility and automation you need to detect issues fast, get notified immediately, and have the tools to diagnose what went wrong.

This roadmap takes you from basic structured logging all the way to a full observability dashboard with alerting and documented response procedures. If you’ve only ever debugged by reading print statements, Bronze will level you up. If you already log effectively, Silver and Gold will show you how monitoring and alerting work at real companies.

**You’ll walk away understanding:** Why structured logging matters, how metrics and alerting work together, and what Production Engineers actually do when they get paged at 3am.

**Note:** Some tools in this roadmap (especially Prometheus and Grafana) require adequate system resources. Docker Compose will help manage the stack, but keep an eye on your machine’s memory.

---

## The Tiers at a Glance

**Bronze: “Visible” (10 pts)** \-\> Implement structured logging, collect basic metrics, and have a manual way to check service status.

**Silver: “Alert Ready” (25 pts)** \-\> Set up automated alerting for service health and resource thresholds.

**Gold: “Incident Ready” (50 pts)** \-\> Build a metrics dashboard, track meaningful metrics, and create response runbooks.

Each tier builds on the one before it. We recommend completing them in order.

---

## Bronze: “Visible”

### What You Need to Do

- Implement structured logging (not just print() statements)  
- Collect basic metrics (CPU, memory, request count)  
- Have a manual way to check service status (dashboard, logs, or CLI)

### Key Concepts

**Structured logging** means your log messages follow a consistent, parseable format rather than being free-form text. Instead of print(“something went wrong”), a structured log entry might include a timestamp, log level, module name, and a descriptive message \- all in a consistent format that tools can parse and search. Flask uses Python’s built-in logging module, which supports structured output out of the box.

The difference matters because structured logs can be filtered, searched, and analyzed programmatically. When you’re looking through thousands of log lines at 3am trying to find what went wrong, the difference between print(“error”) and a timestamped, leveled log entry with context is enormous.

**Metrics** are numerical measurements about your service’s behavior over time. Basic system metrics include CPU usage, memory consumption, and disk space. Application-level metrics include things like request count, response times, and error rates. Collecting metrics gives you a quantitative picture of how your service is performing \- and more importantly, whether it’s getting worse.

For Bronze, you don’t need a fancy monitoring stack. Collecting metrics can be as simple as exposing a /metrics endpoint or logging performance data in a structured format that you can inspect manually.

### Recommended Tools

The tools listed below are suggestions based on what works well with the project template stack. You’re welcome to use alternatives that accomplish the same goals.

- **Python logging module** \- Built into Python, configurable with formatters and handlers. Flask integrates with it via app.logger.  
- **prometheus\_flask\_exporter** \- A Flask extension that automatically exposes request metrics in Prometheus format at a /metrics endpoint.

### Verification (Examples)

- Logs showing structured format (timestamps, levels, context \- not raw print statements)  
- Evidence of metrics being collected (a /metrics endpoint, log output, or similar)  
- A way to manually inspect service status (viewing logs, hitting a status endpoint, etc.)

### Resources

- [Flask Official Logging Documentation](https://flask.palletsprojects.com/en/stable/logging/) \- Configuring Python’s logging module for Flask  
- [Better Stack: Getting Started with Flask Logging](https://betterstack.com/community/guides/logging/how-to-start-logging-with-flask/) \- Practical guide to structured logging in Flask, including formatters and handlers  
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html) \- Official Python guide to the logging module

---

## Silver: “Alert Me”

### What You Need to Do

- Configure alerting to a channel (Slack, Discord, email, webhook)  
- Set up alerts for service down/unhealthy  
- Set up alerts for resource thresholds (high CPU, memory, error rate)  
- Alert triggers should fire within 5 minutes of an issue

### Key Concepts

**Alerting** is the automation that bridges the gap between “something is wrong” and “someone knows about it.” Instead of manually watching dashboards or tailing logs, you configure rules that automatically send notifications when specific conditions are met \- like your service being unreachable, error rates spiking, or CPU usage exceeding a threshold.

Good alerts have a few properties: they fire quickly (within minutes, not hours), they’re actionable (the person receiving the alert knows what to do), and they’re not too noisy (if you get alerts for every minor fluctuation, you’ll start ignoring them \- this is called “alert fatigue”).

**Alert thresholds** are the specific values that trigger an alert. For example, “send an alert if error rate exceeds 5% for more than 2 minutes” or “alert if the health check fails 3 times in a row.” Setting good thresholds is part art, part science \- too sensitive and you get false alarms, too lenient and you miss real issues\!

For this hackathon, a practical approach is to use Prometheus for collecting metrics and its built-in Alertmanager for sending notifications. But simpler approaches work too \- a script that periodically checks your health endpoint and sends a webhook to Discord on failure is a perfectly valid alerting system.

### Recommended Tools

- **Prometheus \+ Alertmanager** \- Prometheus collects and stores metrics; Alertmanager handles alert routing and notifications. Industry standard.  
- **Discord/Slack Webhooks** \- Simple way to receive alert notifications without complex integrations.

### Verification (Examples)

- A test alert triggered and notification received (screenshot or live demo)  
- Alert configuration showing rules for service health and resource thresholds  
- Evidence that alerts fire within 5 minutes of an issue

### Resources

- [Prometheus Alerting Overview](https://prometheus.io/docs/alerting/latest/overview/) \- How Prometheus alerting and Alertmanager work together  
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/) \- Configuring alert routing, receivers, and notification channels  
- [Discord Webhooks Guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) \- Setting up a webhook to receive notifications in Discord  
- [prometheus\_flask\_exporter](https://github.com/rycus86/prometheus_flask_exporter) \- Automatically expose Flask request metrics for Prometheus to scrape

---

## Gold: “Incident Ready”

### What You Need to Do

- Build a dashboard with key metrics visualized (Grafana, Datadog, or similar)  
- Track at least 4 meaningful metrics  
- Write a basic runbook for responding to common alerts  
- Demonstrate the ability to diagnose an issue using your observability tools

### Key Concepts

**A metrics dashboard** is a visual display of your service’s key metrics in real time. Instead of running queries manually or reading raw numbers, a dashboard gives you charts and graphs that show trends at a glance. Grafana is the most widely used dashboarding tool in the PE/SRE world, and it integrates directly with Prometheus.

What makes a metric “meaningful” depends on your service, but a good starting set might include: request rate (how many requests per second your service is handling), error rate (what percentage of requests are failing), response latency (how long requests take), and system saturation (CPU and memory usage). These four are sometimes some of the golden signals of monitoring.

**A runbook** is a document that describes how to respond to specific alerts or incidents. When an alert fires at 3am, the on-call engineer shouldn’t have to figure out what’s going on from scratch. A runbook tells them: what the alert means, what to check first, what the likely causes are, and what steps to take to resolve the issue. Writing good runbooks is one of the most valuable (and underappreciated) skills in Production Engineering.

### Recommended Tools

- **Grafana** \- The industry-standard dashboarding tool. Connects to Prometheus and lets you build rich, interactive dashboards.  
- **Prometheus** \- If you set it up for Silver, your Gold dashboard can visualize the same metrics.

### Verification (Examples)

- A dashboard showing at least 4 meaningful metrics (screenshots or live demo)  
- A runbook in your repository describing how to respond to common alerts  
- A walkthrough showing how you’d diagnose an issue using your observability tools (like “error rate spiked \-\> I checked this dashboard panel \-\> I looked at these logs \-\> I found the root cause”)

### Resources

- [Grafana Getting Started with Prometheus](https://grafana.com/docs/grafana/latest/getting-started/get-started-grafana-prometheus/) \- Setting up Grafana to visualize Prometheus metrics  
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/) \- How to design effective monitoring dashboards  
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) \- Google’s guide to the “golden signals” and effective monitoring  
- [PagerDuty Incident Response Guide](https://response.pagerduty.com/) \- Comprehensive guide to incident response practices and runbook writing

---

## Tips for Your Team

- **Start with structured logging in Bronze \- everything else builds on it.** If your logs are good, debugging gets dramatically easier at every tier.  
- **Split the work.** One teammate can set up logging and the /metrics endpoint while another configures Prometheus and Alertmanager.  
- **Use Docker Compose to run the monitoring stack.** Prometheus, Alertmanager, and Grafana all have official Docker images and compose well together.  
- **Test your alerts.** Don’t just configure them \- trigger them. Kill your service and make sure the alert fires and the notification arrives.  
- **Write the runbook as you build.** When you set up an alert, immediately write down what should happen when it fires. That’s your runbook.

---

---

# Getting Started: Documentation (Bonus) {#getting-started:-documentation-(bonus)}

## What Is This Roadmap About?

Documentation is fundamental to reliable Production Engineering; it’s the difference between a service that only one person can operate and a service that an entire team can maintain, debug, and improve. At real companies, PE teams spend significant time writing and maintaining runbooks, architecture docs, and deployment guides \- because when something breaks at 3am, good documentation is what saves you. 

This bonus category rewards teams who treat documentation as a first-class deliverable, not an afterthought. You can earn these points alongside any roadmap \- and the documentation you write here may also satisfy requirements in other roadmaps (like the failure mode documentation in Reliability Engineering Gold).

**You’ll walk away understanding:** What makes documentation useful in an operational context, and why PE teams invest so heavily in it.

---

## The Tiers at a Glance

**Bronze: “Documented” (10 pts)** \-\> Clear README, architecture diagram, and API documentation.

**Silver: “Operationally Documented” (20 pts)** \-\> Deployment guide, troubleshooting guide, and environment documentation.

**Gold: “Handbook Ready” (35 pts)** \-\> Comprehensive operational documentation including runbooks, scaling considerations, and a decision log.

Each tier builds on the one before it. We recommend completing them in order.

---

## Bronze: “Documented”

### What You Need to Do

- Write a clear README with setup instructions  
- Create an architecture diagram (can be simple)  
- Document your API or endpoints

### Key Concepts

**A good README** answers the questions a new team member would have: What does this project do? How do I set it up locally? How do I run it? What are the key endpoints? It doesn’t need to be long \- it needs to be clear and accurate. If someone can clone your repo and get the app running by following your README, you’ve succeeded.

**An architecture diagram** is a visual representation of how your system’s components fit together. For this hackathon, it might show your Flask app, your database, Nginx, and how they connect. It doesn’t need to be fancy \- a simple boxes-and-arrows diagram drawn in any tool (or even hand-drawn and photographed) is fine. The point is that someone can look at it and quickly understand the shape of your system.

**API documentation** describes what endpoints your service exposes, what they expect as input, and what they return. For a URL shortener, this might cover the endpoint for creating a short link, the endpoint for redirecting, and the health check endpoint. Include the HTTP method, the URL path, expected request body (if any), and what the response looks like.

### Verification (Examples)

- A README in your repo that a new person could follow to get the app running  
- An architecture diagram (in the repo or linked from the README)  
- API/endpoint documentation (can be a section in the README or a separate file)

### Resources

- [Make a README](https://www.makeareadme.com/) \- Guidance and templates for writing effective READMEs  
- [Mermaid.js](https://mermaid.js.org/) \- Create diagrams using simple text syntax (renders directly in GitHub markdown)  
- [Best Practices for API Documentation](https://swagger.io/blog/api-documentation/best-practices-in-api-documentation/) \- What good API docs look like

---

## Silver: “Operationally Documented”

### What You Need to Do

- Write a deployment guide (how to deploy, how to rollback)  
- Create a troubleshooting guide for common issues  
- Document your environment and configuration

### Key Concepts

**A deployment guide** documents the exact steps to deploy your service \- and critically, the steps to roll back if something goes wrong. This should be specific enough that a teammate who didn’t build the deployment pipeline can still deploy safely. Think of it as a recipe: “Run this command, check this URL, verify this output.”

**A troubleshooting guide** anticipates common problems and tells someone how to diagnose and fix them. “If the service returns 500 errors, check the database connection.” “If the health check is failing, verify the container is running.” You build this guide from your own experience during the hackathon \- every time you hit a problem and solve it, write down what happened and how you fixed it.

**Environment and configuration documentation** describes the settings, environment variables, secrets, and dependencies your service needs to run. If your app requires a DATABASE\_URL environment variable, a Redis connection string, and a specific Python version \- document all of that. Future-you (or your teammate) will thank you.

### Verification (Examples)

- A deployment guide in your repository (step-by-step, including rollback)  
- A troubleshooting guide covering common issues you encountered  
- Documentation of environment variables, configuration, and dependencies

### Resources

- [Write the Docs: Documentation Guide](https://www.writethedocs.org/guide/) \- Community-driven guide to writing good technical documentation  
- [12-Factor App: Config](https://12factor.net/config) \- Best practices for managing application configuration through environment variables

---

## Gold: “Handbook Ready”

### What You Need to Do

- Complete all Silver requirements, plus:  
- Write runbooks for incident response (what to do when alerts fire)  
- Document capacity and scaling considerations  
- Create a decision log explaining key technical choices and potential technical debt

### Key Concepts

**Runbooks** are step-by-step guides for handling specific operational scenarios. They answer questions like: “What do I do when the database connection alert fires?” or “How do I investigate high memory usage?” A good runbook has a clear trigger (when to use it), diagnostic steps (how to figure out what’s wrong), remediation steps (how to fix it), and escalation instructions (who to contact if you can’t fix it).

**Capacity and scaling documentation** describes your system’s current limits and how to expand them. How many concurrent users can your service handle? What’s the bottleneck? What would you need to change to support 10x the traffic? This kind of documentation helps teams plan ahead rather than react to outages.

**A decision log** records the key technical choices you made during the hackathon and why you made them. “We chose Redis for caching because it integrates easily with Flask and supports TTL expiration.” “We used Nginx as a reverse proxy instead of HAProxy because the team had more experience with it.” Decision logs also note known trade-offs and technical debt: “We hardcoded the database URL for now \- this should be moved to an environment variable before production.”

### Verification (Examples)

- Runbooks in your repository for at least 2-3 operational scenarios  
- A capacity/scaling document describing current limits and how to grow  
- A decision log with key technical choices, rationale, and known trade-offs  
- A walkthrough explaining how a new team member would use the documentation

### Resources

- [PagerDuty Incident Response Documentation](https://response.pagerduty.com/) \- Real-world examples of operational documentation and runbooks  
- [Google SRE Book: Documenting Failure](https://sre.google/sre-book/postmortem-culture/) \- How Google approaches postmortems and operational learning  
- [ADR (Architecture Decision Records)](https://adr.github.io/) \- A lightweight format for documenting technical decisions

---

## Tips for Your Team

- **Start your README on day one.** Even a rough outline is better than starting from scratch at the end.  
- **Assign a “docs owner.”** One teammate should be responsible for keeping documentation updated as the project evolves \- though everyone should contribute.  
- **Write docs as you solve problems.** Every bug you fix, every deploy you do, every configuration you change is documentation material. Capture it in the moment.  
- **Keep it practical, not pretty.** A plain markdown file with accurate, useful information beats a beautifully formatted document with outdated content.  
- **Think about the reader.** The best test for documentation: could a teammate who just joined your team use it to understand and operate the service?

