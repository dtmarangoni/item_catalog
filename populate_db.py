from database import db_session, User, Category, Item


def populate_db():
    """Populate the DB with some initial data.
    It will be added an example user, some categories and items.
    """
    user = User(username='carlos', email='carlos@email.com',
                picture='mypicture')
    user.hash_password('123456')
    db_session.add(user)
    db_session.commit()

    category = Category(name='Soccer')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Basketball')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Baseball')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Frisbee')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Snowboarding')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Rock Climbing')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Foosball')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Skating')
    db_session.add(category)
    db_session.commit()
    category = Category(name='Hockey')
    db_session.add(category)
    db_session.commit()

    category = db_session.query(Category).filter_by(name='Snowboarding').one()
    item = Item(name='Snowboard',
                description='Best for any terrain conditions',
                category_id=category.id)
    db_session.add(item)
    db_session.commit()

    category = db_session.query(Category).filter_by(name='Soccer').one()
    item = Item(name='Soccer ball',
                description='An inflated ball used in playing soccer.',
                category_id=category.id)
    db_session.add(item)
    db_session.commit()

    category = db_session.query(Category).filter_by(name='Baseball').one()
    item = Item(name='Bat',
                description='A smooth wooden or metal club used to hit the '
                            'ball after it is thrown by the pitcher.',
                category_id=category.id)
    db_session.add(item)
    db_session.commit()

    category = db_session.query(Category).filter_by(name='Hockey').one()
    item = Item(name='Hockey Skates',
                description='Made with metal blades attached underfoot and '
                            'used to propel the bearer across a sheet of ice '
                            'while ice skating.',
                category_id=category.id)
    db_session.add(item)
    db_session.commit()

    category = db_session.query(Category).filter_by(name='Frisbee').one()
    item = Item(name='Disc',
                description='A frisbee disc with size of 175 gram disc.',
                category_id=category.id)
    db_session.add(item)
    db_session.commit()

    print('Database populated.')


# When running this module from command line it will populate the DB with some
# example data.
if __name__ == '__main__':
    populate_db()
