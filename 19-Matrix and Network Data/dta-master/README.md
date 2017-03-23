# DTA Anyway! #
_Dynamic Traffic Assignment project hosting for the SFCTA/FHWA/PB open source DTA research project._

---


## Webinar ##
  * [Presentation](http://dta.googlecode.com/files/DTA_Anyway_Webinar_Nov_30_2012_updatedCPUtime.pdf)
  * [Webinar recording](http://code.google.com/p/dta/downloads/detail?name=SFDTA_Webinar_Nov30_2012.vcr&can=2&q=#makechanges) and [required software to listen to webinar recording](http://code.google.com/p/dta/downloads/detail?name=ATT_Connect_Participant.msi&can=2&q=#makechanges)

## Final Reports ##
  * [Final Methodology Report](http://code.google.com/p/dta/downloads/detail?name=SFDTAFinalMethodologyReport_113012.pdf&can=2&q=#makechanges)
  * [Final Calibration and Validation Report](http://code.google.com/p/dta/downloads/detail?name=SFDTAFinalCalibrationandValidationReport113012.pdf&can=2&q=#makechangess)
  * [Future Research Topics Report](http://code.google.com/p/dta/downloads/detail?name=SFDTAFutureResearchTopicsReport.pdf&can=2&q=#makechanges)
  * [Analysis of Applications Report](http://code.google.com/p/dta/downloads/detail?name=SFDTAAnalysisofApplications.pdf&can=2&q=#makechanges)

## Interim Reports ##
  * [Preliminary Calibration and Validation Report](https://code.google.com/p/dta/downloads/detail?name=SF%20DTA%20Model%20Calibration%20and%20Validation%20WorkingDraftToPeerReviewPanel.pdf&can=2&q=#makechanges)
  * [Integration Options Report](https://code.google.com/p/dta/downloads/detail?name=SF%20DTA%20Model%20Integration%20Options%20Jul-13_FinalWorkingDraftForPeerReviewPanel.pdf&can=2&q=#makechanges)

## Useful Links ##

! This is a model development project.  For official SFCTA forecasts, please see the [sfcta model service bureau homepage](http://www.sfcta.org/modeling-and-travel-forecasting/model-data-service-bureau).

[I want the code!](http://code.google.com/p/dta/wiki/UsingTheCode)

[What is this "DTA" thing, anyway?](http://code.google.com/p/dta/wiki/WhatIsDTA)

[Code Documentation](http://dta.googlecode.com/git-history/dev/doc/_build/html/index.html)
[DTA Software Information](http://code.google.com/p/dta/wiki/Software)

## Tasks ##

  1. [Project Management](http://code.google.com/p/dta/wiki/TaskOne)
  1. [DTA Model Development](http://code.google.com/p/dta/wiki/TaskTwo)
  1. [Analysis Tools Development](http://code.google.com/p/dta/wiki/TaskThree)
  1. [Model Applications](http://code.google.com/p/dta/wiki/TaskFour)
  1. [Evaluation and Final Reporting](http://code.google.com/p/dta/wiki/TaskFive)


---

## Related Projects ##
  * [CountDracula](https://github.com/sfcta/CountDracula) a count management system
  * [TAutils](http://github.com/sfcta/TAutils) Utilities we use with SF-CHAMP


## Project Status and Updates ##

For weekly updates on what we are up to: [Project Status page](http://code.google.com/p/dta/wiki/ProjectStatus) or [Calendar page](http://www.google.com/calendar/embed?src=sfcta.org_bitt2f8attbqp8kffefijm7ln0%40group.calendar.google.com&ctz=America/Los_Angeles)

**August/September**

The project team conducted multiple sensitivity tests across several axes including: network supply, traffic flow parameters, and random number seeds.  During the sensitivity testing of the traffic flow parameters, an error was discovered in the interpretation between the observed data and the parameters used in Dynameq.  Thus, several weeks have been spent re-adjusting these parameters after it was found that directly using the observed values created gridlock.

The peer review panel assembled a list of short-term tasks, which the project team documented on the wiki and prioritized.  This included suggestions such as the inclusion of a distance term in the generalized cost function, implementing an even lower facility type than 'local', and a different methodology to calculate free flow speeds for segments with unsignalized intersections.

The team grappled with some gridlock introduced by trucks, and thus adjusted some of the default vehicle types and PCU factors to better match the type of trucks that are found on the streets of San Francisco during peak hours.

CountDracula was updated to use the GeoDjango framework and was staged on a server machine along with Dynameq.  CountDracula now allows us to visually see where counts are  in order for us to prioritize further count standardization.

At the suggestion of the Peer Review Panel, we employed some interns to standardize more counts and truck counts to use in validation.  We also added more counts that we currently use in our SF-CHAMP validation.

**June / July**

The majority of this reporting period included making numerous calibration runs per week and evaluating whether the changes in each run improved the validation statistics and made sense.  A specific wiki page was developed to track all the validation runs that were deemed useful enough to ‘keep’.

Early calibration runs identified numerous network coding issues surrounding intersection geometries.  To alleviate some of these issues, a network coding override file was developed to explicitly identify any intersection where angles alone were not enough to determine which movement was what.  This particularly helped for issues near Market Street, a major street that cuts diagonally through the city’s core grid network.  We also continued making road network refinements in the cube network and made additional edits to transit files as they were required.  Experimented with various generalized cost functions. Experimented with various levels of demand by increasing it wholesale by 10 and 30 percent.

This period included significant field and data analysis to estimate traffic flow model parameters based on observed data in San Francisco by slope, area type, and facility type.  The data collection effort included observations of traffic flow behavior at nine locations and the assembly of preexisting speed survey data recorded at over 500 locations.  Significant improvements to the model validation were realized and documented in the form of a TRB paper submitted to the Annual Meeting as well as online at the project website.  Additionally, we calibrated freeway traffic flow models to PeMS ITS data.

Enabled Count Dracula to aggregate counts to time period and developed scripts to generate validation reports for both counts and travel times in a semi-automated fashion.

Network and code development tasks included implementing transit lanes into the network coding. Further standardizing the unit test testing suite including documentation.

Reporting tasks completed included writing a draft Validation and Calibration report, Integration Strategies report for the Peer Review Panel to comment on, and developed an associated power point presentation.  All are available online at the project website.  We also significantly updated the DTA Anyway code documentation for the Peer Review Panel to comment on, and developed an associated power point presentation. Both are available online at the project website.

On July 25th 2012, we held a Peer Review Panel meeting with five panelists, the Dynameq software developer, and local agency partners in attendance.  An official TMIP report from the meeting is pending.


**April / May**

The team completed several calibration runs, which highlighted several network issues.  Many of the network issues occurred at awkwardly angled intersections where the code base was unable to correctly identify the movement (left turn, through, right turn, etc.) based on the angle and street names. To solve this problem, we developed a movement override file and now read this in at the same time as the cube network.  A multitude of other network issues were fixed in the static network including the treatment of divided streets, the minimum link distance, and numerous turn restrictions.  The transit line file had to be updated to reflect all of these network changes.  At this time, we have successfully removed all gridlock from the network, have convergence at around 1% for 50 iterations of DTA, and have a maximum of around 20 vehicles waiting to enter the network.

The functional types from our static network were translated to the DTA network.  The initial values for speeds and capacities were developed based on our static network freeflow speeds, plus 5mph to represent the fact that the static free flow speeds included intersection delay.  Capacities on DTA networks do not often come in to play directly, because the flow propagation parameters (freeflow speed, jam density, and backward shockwave speed) are reflected into the model separately, so we set them fairly high for now and did not worry so much about getting them exactly correct.  After an initial validation run using the initial traffic flow parameters based on area type and functional type, we identified the need to more robustly represent roadway slope in the speed-flow curves.  A literature review revealed little, if any, useful data, so we planned a data collection effort to take place in June.

For validation, the team imported all standardized counts to CountDracula and made sure CountDracula worked with DTA Anyway.

The programming team finished cleanups and code reviews of all signal and transit classes. The algorithms for external centroid connector placement and size were fixed based on issues identified in the first validation run and now are sized to reflect the size of the links that they represent (i.e. a 5 lane freeway). The signal matching code was updated to match more signals and to use the movement override file, which now is able to handle 1,093 signals.  Additional issues with the signal code were identified and fixed based on the validation runs, including the incorrect coding of some left turns and right turns as permitted instead of protected. Validation scripts were updated. In particular, the team added functionality to the CorridorPlot module to include SVG output, the ability to show incoming and outgoing link flows, and link capacity.

We've also successfully applied for a TMIP Peer review, which will be conducted July 25th, 2012.

**February / March**

Performed the first successful DTA calibration run simulating 100% of the 3-hour subarea demand of the SF-CHAMP model (year 2011). The average relative gap after 50 iterations and 15 hours of execution time is 7% with a consistent tendency to decrease. While there is no apparent gridlock, there are a few thousand vehicles waiting to enter the network when the loading stops. There are a few easy-to-spot areas with unreasonable flows that we plan to address first before proceeding further with the calibration. Earlier calibration runs with 50% and 75% of the demand had tight gaps and very few waiting trips. Significant gridlock that occurred in an initial test run of 100% demand was due to the incorrect placement and lane count of centroid connectors in relation to freeway ramps and external links. After addressing these issues manually we were able to complete the 50%, 75%, and 100% demand run mentioned above. We plan to update the centroid connector placement script to take into account facility type and boundary links to avoid similar problems in the future.

We have finished standardizing the format of 800 excel files containing 15-minute movement counts for 800 intersections in our study area. The next step will be to map each intersection to a node in our network and update the CountDracula count database. We also made several updates and conducted consistency and compatibility checks in the code that have increased its coherence and readability. We have attached vehicle class prohibitions to movement objects and have been able to partially address the vehicle restrictions in our network. Further work may be needed to ensure that portions of code such as the shortest path algorithms take into account turn prohibitions for different vehicle classes.

We have added two transit modules for Cube and Dynameq transit routes. The Cube module reads transit routes in the TPPlus format using a parser with syntax similar to regular expressions. The Dynameq transit module reads and writes route files in the Dynameq format. An adaptor method was written that converts a Cube transit route to a Dynameq route containing the same node IDs. In order to ensure that the converted Dynameq route consists of a valid sequence of nodes we used a shortest path algorithm to connect the disconnected components of the converted Dynameq transit route.

Started writing scripts that generate plots of our simulation results.

**December / January**

Using the python scripts that read the excel signal cards we imported 750 signals (out of the 1,200) into the DTA software and performed an assignment. All the information contained in a signal cards was imported to the DTA software including offset, cycle time and green, yellow, and red timings for each phase in the signal card. In our simulation, a gridlock occurred at the 30th iteration of our assignment and did not dissolve in subsequent iterations. Modifications in the network geometry and the equilibration parameters will help us resolve the problem.

Often, the network geometry of a planning network needs to be modified in order to be compatible with what can be simulated in a DTA model or optimized in Synchro. Our planning network in particular locations often had more links represented than would be appropriate in DTA. Common examples in San Francisco are the angled intersections on Market Street that are represented by up to three nodes in our original planning network. To simplify signal operations, reduce the number of small links, and achieve compatibility with the existing Synchro models we simplified complex intersections to one, or a maximum of two nodes. These edits were made to the planning network and not the DTA network in order to maintain direct compatibility and seamless translation between the two using our utilities. Throughout this process we have taken note of several basic dos and don’ts for planning networks in order to transition them to valid DTA networks, and we will publish these on our website.

We were able to programmatically map over 1,000 signal cards to the appropriate intersections in our DTA network using only the street name information with almost no errors. We plan to revise the street names in our network or in the remaining signal cards so that we match all the signal cards in our disposal. Building this direct translation between all of our signalized intersections and the standard format that SFMTA keeps their signals in allows us to relatively seamlessly update our timings based on any new information we receive from SFMTA.  As of now 26 signals do not match programmatically, and we have 79 signals remaining to review and see if we can modify the planning network or code in order to get them to match.

In the excel signal cards there was no distinction between protected and permitted movements. To overcome this limitation, we made algorithmic improvements in our code that allows us to geometrically distinguish between non-conflicting movements such as two opposing through movements and the ones that intersect with each other. Such a distinction is necessary because the simulated vehicles executing a permitted movement that conflicts with a higher priority movement have to wait for the appropriate gap on the later one.

We have added more functionality into our code base that allows us calculate the capacity of a movement based on its type (protected vs. permitted) and the green time that is allocated to it. We have also prepared network-wide GIS layers in which we plot the signal attributes of each intersection in our model. Based on our preliminary checks we verified that we have correctly imported the vast majority of the excel cards to the DTA software. We envision that the tools we have been developing will help us to easily identify signalized intersections that have incorrect attributes and limit the capacity of a corridor.

Code review was not happening as regularly or rigorously as in the beginning of the project, but we have picked that back up again with a vengeance post-holidays and are starting with the ‘scripts’ section of the code base.

**October / November**

We focused most of our time in this reporting period on importing signals into the DTA model. Our study region has approximately 1,200 signals, each of which has their signal timings stored in an individual spreadsheet containing complete phasing and time-of-day data. We estimated from past experience that it will take us about 15 minutes to manually import a signal for a single time period without taking into account any network edits that need to be made. Given that we eventually want to model more than one time period, we figured that importing the signals manually would take too much time (about 300 hours) and would not be replicable for other time periods. Instead, we decided to develop a program that reads all the movement, timing and phasing information and builds the corresponding Dynameq timing plan from the semi-structured spreadsheet.

  * Developed and later refined algorithms that match signal timing card spreadsheets (the format in which all San Francisco traffic signals are kept) with DTA nodes. We used Google Maps to associate a node to an intersection identified by the cross street names and we also wrote a string matching algorithm that associates the street names in the planning network with the ones stored in the excel cards. We found that the latter approach was more successful allowing us to associate as many as 80% of the signalized intersections, a success rate that was raised slightly with subsequent revisions to the algorithm. Nodes that were unable to be matched by refining the algorithm will be matched by hand.
  * Developed and refined algorithms that read the different sections of the excel signal card into a signal object. Due to the semi-structured way the information was contained in the cards we ended up using keywords to signify section boundaries and allowed the algorithm to scan a range of cells to locate the appropriate information. We built a table data structure that stores the state (green, yellow, read) of each movement by time and an algorithm that aggregates state across multiple movements to identify the active phase at each point in time.
  * Developed and refined algorithms that read the signal timing cards in their excel format and match movements in the signal card with movements in the DTA network based on street name and orientation (such as EB or EBLT). Movements that failed to match were analyzed for common causality.  For reasons that were easy to fix, or that affected a great deal of movements, the signal card reading script was improved to address them.  Movements that were unable to be matched by a reasonably-refined algorithm will be matched by hand.
  * Refactored the signal representation in the DTA Python library and added new functionality that allowed us to test if a signal contains any errors before importing it to Dynameq. Errors we were able to identify include a) missing movements from the signal b) invalid green, yellow, red or offset times.
  * Updated the DTA Python library representation of turn penalties and link shapes.

**September**
  * Created the demand class that reads, writes and manipulates Dynameq and Cube trip matrices. The demand object internally stores trips in a multidimensional labeled array that enables us to efficiently use non consecutive integers as zone ids. This structure will allow us to perform operations on portions of the demand matrix transparently and efficiently.
  * Wrote an algorithm that checks that a feasible path exists between each OD pair without building a shortest path tree for each origin. The algorithm depends on the computationally cheaper depth-first algorithm which we execute twice to build a meta-graph that defines the connectivity of our network.
  * Developed an algorithm that merges two transportation networks with conflicting node or link ids and zero user interaction. The algorithm draws a polygon around one of the networks and copies all elements of the other network that are outside or cross the polygon boundary. To implement this algorithm we developed some computational geometry algorithms such as convex-hull and point-in-polygon. The merge algorithm will allow us to have two or more modelers modify different parts of the network at the same time and seamlessly merge their changes. We will also use the algorithm to merge our older DTA network to the county network that comes from Cube.
  * Programmatically or manually resolved all Dynameq import errors. Our scripts read a Cube network and produce the corresponding error-free Dynameq one taking into account requirements that Dynameq has about network geometry such as overlapping links.
  * Implemented link shape
  * Added functionality to our base network class that allows us to export our node and link elements (Dynameq or Cube) to ESRI shapefiles for easy viewing.
  * Implemented turn prohibitions
  * Updated documentation
  * **Made successful countywide test runs** (gap 2 to 3%) involving up to 600K trips distributed evenly in the study area over a 3-hour period. The number of links in the network is 38 thousand and the number of nodes 12 thousand. There were no gridlocks or significant loading problems and all traffic entered and exited the network as expected.


**August**
  * Created and then enhanced network merge algorithm to address connectivity issues at the boundary of the merged networks
  * Developed algorithm that removes centroid connectors from intersections on the entire network, and then creates new centroid connectors.
  * Enhanced the centroid connector creation algorithm to be configurable and smarter about where it is attaching centroid connectors to avoid conflicts at entry and exit locations. As a result, we eliminated queues or gridlocks at entry/exit points in our test runs.
  * Updated scripts to address updated Dynameq ASCII format
  * Brainstormed how to implement demand class
  * Various code reviews
  * Write detailed documentation and produced updated Sphinx documentation
  * Tested all algorithms with our current data

**July**
  * Created Count Dracula
  * Uploaded Counts to Count Dracula
  * Tested accessor scripts to counts in Count Dracula that allow you to match it to the DTA network without relying on node numbers or streetnames.
  * Finalized network import scripts
  * Started working with the 64-bit version of Dynameq that should be able to load and run our entire network no problem.
  * Wrote lots of unit tests.

**June**
  * Wrote [APIs](http://code.google.com/p/dta/wiki/APIdiscussion) to help distill what parts of original  code base we needed
  * Created [Functional Spcs](http://code.google.com/p/dta/wiki/NetworkImportFunctionalSpec) and UMLs to distill class relationships and methods
  * Started [CountDracula](http://github.com/sfcta/CountDracula/) project to import and organize our traffic counts
  * Finalized consultant task-order
  * Finalized purchase order for expanding Dynameq software

**May**
  * Discussed and finalized [software licensing](http://code.google.com/p/dta/wiki/SourcePolicies) decision


---

## About the Project ##

This project is funded by the [U.S. Federal Highway Administration](http://www.fhwa.dot.gov) and with local matching funds from the [San Francisco County Transportation Authority](http://www.sfcta.org)
