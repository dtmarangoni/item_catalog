#!/usr/bin/env python3
#
"""Module to populate database with example info."""

import json

from database import db_session, User, Category, Item


def populate_db():
    """Populate the DB with some initial data.

    It will be added an example user, some categories and items.
    """
    user = User(username='carlos', email='carlos@email.com',
                picture='mypicture')
    user.hash_password('123456')
    db_session.add(user)

    catalog_json = json.loads("""
        {"Catalog": 
            [{"Item":
                [{"category_id": 1,
                  "description": "An inflated ball used in playing soccer.",
                  "id": 2,
                  "name": "Soccer ball",
                  "user_id": 1
                  },
                 {"category_id": 1,
                  "description": "Item of clothing worn on the feet and often covering the ankle or part of the calf.",
                  "id": 3,
                  "name": "Socks",
                  "user_id": 1
                  }],
              "id": 1,
              "category": "Soccer"
              },
             {"Item": [],
              "id": 2,
              "category": "Basketball"
              },
             {"Item":
                 [{"category_id": 3,
                   "description": "A smooth wooden or metal club used to hit the ball after it's thrown by the pitcher",
                   "id": 4,
                   "name": "Bat",
                   "user_id": 1
                   }],
              "id": 3,
              "category": "Baseball"
              },
             {"Item":
                [{"category_id": 4,
                  "description": "A frisbee disc with size of 175 gram disc.",
                  "id": 6,
                  "name": "Disc",
                  "user_id": 1
                  }],
              "id": 4,
              "category": "Frisbee"
              },
             {"Item":
                [{"category_id": 5,
                  "description": "Best for any terrain conditions",
                  "id": 1,
                  "name": "Snowboard",
                  "user_id": 1
                  }],
              "id": 5,
              "category": "Snowboarding"
              },
             {"Item": [],
              "id": 6,
              "category": "Rock Climbing"
              },
             {"Item": [],
              "id": 7,
              "category": "Foosball"
              },
             {"Item": [],
              "id": 8,
              "category": "Skating"
              },
             {"Item":
                [{"category_id": 9,
                  "description": "Made with metal blades attached underfoot and used to propel the bearer across a sheet of ice while ice skating.",
                  "id": 5,
                  "name":
                  "Hockey Skates",
                  "user_id": 1
                  }],
              "id": 9,
              "category": "Hockey"
              }]
         }""")

    for c in catalog_json['Catalog']:
        category = Category(id=c['id'], name=c['category'])
        db_session.add(category)
        for i in c['Item']:
            item = Item(id=i['id'], name=i['name'],
                        description=i['description'],
                        category_id=i['category_id'],
                        user_id=i['user_id'])
            db_session.add(item)

    db_session.commit()
    print('Database populated.')


# When running this module from command line it will populate the DB with some
# example data.
if __name__ == '__main__':
    populate_db()
