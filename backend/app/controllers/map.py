async def get_regions(body, db, current_user):
    query = "SELECT ST_AsGeoJSON(top_left), ST_AsGeoJSON(bottom_right), name FROM regions"
    rows = await db.fetch(query)
    return {
        'success': True,
        'data': [{"top_left": row[0], "bottom_right": row[1], 'name': row[2]} for row in rows],
        "message": None,
        "successMessage": None
    }
