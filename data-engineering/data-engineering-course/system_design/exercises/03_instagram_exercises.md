# Exercises — Instagram

## 1. Add a "people you may follow" recommender
Suggest users based on mutual follows.

## 2. Add likes
There is `like`; add the inverse: `GET /api/photos/<id>/likers`.

## 3. Add comments
1:N relationship. `POST /api/photos/<id>/comments`, `GET /api/photos/<id>/comments`.

## 4. Add image storage
Don't fake `image_url` — actually accept base64 in upload, decode,
write to `var/blobs/`, and serve via `/blobs/<id>.jpg` route.

## 5. Add a celebrity hybrid
If a user has >10k followers, don't fanout on write. Instead, on
read, merge their photos into the feed at query time.

## 6. Add explore ranking
Compute "trending photos" = photos in last 24h with high like rate.

## 7. Add pagination cursors
Replace `?limit=20` with `?cursor=<photo_id>&limit=20`.

## 8. Add a stories feature
24-hour ephemeral content. `POST /api/stories`, `GET /api/users/<id>/stories`
(only if < 24h old).
