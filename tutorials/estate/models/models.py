from odoo import fields, models


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"

    id = fields.Integer("Id", readonly=True)
    create_uid = fields.Many2one("res.users", "Created by", readonly=True)
    create_date = fields.Datetime("Created Date", readonly=True)
    write_uid = fields.Many2one("res.users", "Last Updated by", readonly=True)
    write_date = fields.Datetime("Last Updated", readonly=True)
    name = fields.Char("Name", required=True)
    description = fields.Text("Description")
    postcode = fields.Char("Postcode")
    date_availability = fields.Date("Availability Date")
    expected_price = fields.Float("Expected Price", digits=(14, 2))
    selling_price = fields.Float("Selling Price", digits=(14, 2))
    bedrooms = fields.Integer("Bedrooms", required=True)
    living_area = fields.Integer("Lving Area (m2)")
    facades = fields.Integer("Number of Facades")
    garage = fields.Boolean("Garage")
    garden = fields.Boolean("Garden")
    garden_area = fields.Integer("Garden Area (m2)")
    garden_orientation = fields.Char("Garden Orientation")

    _sql_constraints = [
        # 定义一个外键约束，create_uid引用res.users表的id
        (
            "create_uid_foreign_key",
            "FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL",
            "Invalid create user!",
        ),
        # 定义一个外键约束，write_uid引用res.users表的id
        (
            "write_uid_foreign_key",
            "FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL",
            "Invalid write user!",
        ),
    ]
