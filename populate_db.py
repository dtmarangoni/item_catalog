#!/usr/bin/env python3
#
"""Module to populate database with example info."""

import json

from database import db_session, User, Category, Item


def populate_db():
    """Populate the DB with some initial data.

    It will be added an example user, some categories and items.
    """

    catalog_json = json.loads("""
        {"Catalog": 
            [{"Item":
                [{"description": "An inflated ball used in playing soccer.",
                  "name": "Soccer ball"
                 },
                 {"description": "Item of clothing worn on the feet and often covering the ankle or part of the calf.",
                  "name": "Socks"
                  }],
              "category": "Soccer"
              },
             {"Item": [],
              "category": "Basketball"
              },
             {"Item":
                 [{"description": "A smooth wooden or metal club used to hit the ball after it's thrown by the pitcher",
                   "name": "Bat"
                 }],
              "category": "Baseball"
              },
             {"Item":
                [{"description": "A frisbee disc with size of 175 gram disc.",
                  "name": "Disc"
                }],
              "category": "Frisbee"
              },
             {"Item":
                [{"description": "Best for any terrain conditions",
                  "name": "Snowboard"
                }],
              "category": "Snowboarding"
              },
             {"Item": [],
              "category": "Rock Climbing"
              },
             {"Item": [],
              "category": "Foosball"
              },
             {"Item": [],
              "category": "Skating"
              },
             {"Item":
                [{"description": "Made with metal blades attached underfoot and used to propel the bearer across a sheet of ice while ice skating.",
                  "name": "Hockey Skates"
                }],
              "category": "Hockey"
              }]
         }""")

    user = User(username='carlos', email='carlos@email.com',
                picture='mypicture')
    user.hash_password('123456')
    db_session.add(user)
    db_session.commit()

    for c in catalog_json['Catalog']:
        category = Category(name=c['category'])
        db_session.add(category)
        db_session.commit()
        for i in c['Item']:
            item = Item(name=i['name'],
                        description=i['description'],
                        category_id=category.id,
                        user_id=user.id)
            db_session.add(item)
            db_session.commit()

    print('Database populated.')


# When running this module from command line it will populate the DB with some
# example data.
if __name__ == '__main__':
    populate_db()
