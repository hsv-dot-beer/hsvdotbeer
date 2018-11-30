# Rooms

These are areas within venues that serve beer/cider/mead/... via taps.

Most venues will only have one room, but larger venues that have different bars,
such as an indoor bar and an outdoor one, may not serve all beers to patrons in
all rooms. This requires the venue to take advantage of the API provider's
room functionality, if available.

## Creating a Room

**Request**:

`POST` `/api/v1/venues/rooms/`

Parameters:

Name              | Type        | Required | Description
------------------|-------------|----------|------------
name              | string      | Yes      | A friendly name for the room (e.g. Patio)
venue_id          | foreign key | Yes      | The primary key of the venue (e.g. 332)
description       | string      | No       | More information about the room
