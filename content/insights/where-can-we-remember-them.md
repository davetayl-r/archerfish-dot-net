---
title: 'Where can we remember them?'
date: 2015-11-11
heroHeading: 'Where can we remember them?'
heroBackground: 'images/1447156360860-7ITGI1TUHFV4WCCIW5OU_image-asset.jpeg'
slug: where-can-we-remember-them
draft: false
---

Ninety-seven years ago to the day, after more than four years of continuous fighting, the guns of the Western Front fell silent and an armistice was signed. In the years following the end of the First World War the moment when hostilities ended has become synonymous with the remembrance of those who died in the world wars.

To commemorate Remembrance Day this year we’ve used data from the [Commonwealth War Graves Commission](http://www.cwgc.org/) (CWGC) to plot the location of cemeteries and memorials to Commonwealth soldiers who died whilst on active service during the First and Second World Wars. These soldiers served and died in places far from home, from Gallipoli to Nigeria.

From Murmansk to Turkmenistan and Gaza to Waziristan every war memorial tells a story. We encourage you to use our app to uncover one. You can select one or more countries and run our animated map for either the First or Second World War. Each circle represents the number of casualties that are commemorated at that location for that date per country, with the size relative to the number of casualties. If you pause the animation and click on a circle, you can zoom to locate the memorial and follow a link in the popup to the CWGC website to learn more about it.    

By arranging these data as a time series we sought to show the scale of the daily casualties that were suffered during the stalemate battles of the Western Front. Some of these are well known, others are not. In preparing the data we began investigating various spikes in the time series and began searching for their proximate causes. 

We found it surprising to learn that Australia’s darkest day in World War I occurred at the unheralded [Battle of Broodseinde](https://en.wikipedia.org/wiki/Battle_of_Broodseinde) with 6,423 casualties. United Kingdom forces, by contrast, suffered those sorts of casualties with alarming regularity.   

The disparate theatres of conflict and smaller scale battles in the Second World War don't show the same pronounced spikes as the First World War data. A notable exception is the Fall of Singapore, where the British Indian Army suffered their worst casualties of the war. 

The app highlights campaigns and battles overlooked by history. We read into the exploits of the UK’s [Fourteenth or ‘Forgotten’ Army](https://en.wikipedia.org/wiki/Fourteenth_Army_%28United_Kingdom%29) after observing the heavy casualties that they sustained during the Burma Campaign. 

Some historical quirks emerged from the data, we were particularly surprised to learn that the British Indian Army kept fighting following the Japanese surrender, as they were called into fight against pro-Independence Indonesian forces in the [Battle of Surabaya](https://en.wikipedia.org/wiki/Battle_of_Surabaya) during the Indonesian National Revolution.

### On data limitations

The data for this app was sourced from the CWGC [casualty database](http://www.cwgc.org/find-war-dead.aspx) which records the names and place of commemoration of the over 1.7 million men and women who died serving in British Commonwealth forces during the First and Second World Wars.

The database also records the details of 67,000 Commonwealth civilians who died ‘as a result of enemy action’ in the Second World War.

Readers may note that the total casualty counts in the time series charts don’t appear to reflect the total casualty counts reported in official figures nor were significant battles fought at every location indicated on the map. There are multiple reasons for this.

As our app is based on a time series we excluded all records that did not report a date of death. This resulted in us excluding memorials to those who were missing in action where no date could be provided. In other cases where an obviously incorrect ‘dummy date’ was provided were also excluded – for example all of the Indian soldiers commemorated at the [India Gate](http://www.cwgc.org/find-a-cemetery/cemetery/142700/DELHI%20MEMORIAL%20%28INDIA%20GATE%29) in Delhi for their service in the First World War were reported as having died on the first day of hostilities.

The map was designed to show the locations where individuals were commemorated, often that is close to where they may have perished and as a result the map can roughly approximate the locations of the heaviest casualties. However this is not always the case.

In many cases individuals are commemorated far from where they perished, this is particularly apparent for some naval casualties or for those who died during captivity as prisoners of war. For example the HMAS Sydney which was lost with all hands on 19 November 1941 off the coast of Western Australia is commemorated at the [Plymouth Naval Memorial](http://www.cwgc.org/find-a-cemetery/cemetery/142001/PLYMOUTH%20NAVAL%20MEMORIAL) in the UK.

The CWGC records commemorations based upon which national army an individual served with rather than the citizenship of the individual. Since many colonial volunteers enlisted in locally raised regiments such as the King’s African Rifles or the Malay Regiment that served under British command they are commemorated as having served with United Kingdom forces. Likewise American volunteers who enlisted with Canadian forces to fight in the First World War would be commemorated as having served with Canada.  

With these limitations in mind, we hope you enjoy

Lest we forget. 

## Credits:

**Produced by:** [Andrew Taylor](https://au.linkedin.com/in/andrewretaylor), [Dave Taylor](https://au.linkedin.com/in/djataylor) and [Louis Durant](https://au.linkedin.com/in/louisdurant).

**Data source:** Commonwealth War Graves Commission

**Platform:** For the technically minded our app was built using [R](https://www.r-project.org/) and [Shiny](http://shiny.rstudio.com/) using the [Leaflet](https://rstudio.github.io/leaflet/) and [Dygraphs](https://rstudio.github.io/dygraphs/) packages.

If you have questions about our app or want report an error drop us a line at: [info@archerfish.net](mailto:info@archerfish.net) or flick us a tweet @archerfish.
