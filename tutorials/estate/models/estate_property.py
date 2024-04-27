from odoo import fields, models


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"

    id = fields.Integer("Id", readonly=True)
    create_uid = fields.Many2one("res.users", "Created by", readonly=True)
    create_date = fields.Datetime("Created Date", readonly=True)
    write_uid = fields.Many2one("res.users", "Last Updated by", readonly=True)
    write_date = fields.Datetime("Last Updated", readonly=True)
    name = fields.Char("Name", required=True, default="Unknown")  # 名称
    last_seen = fields.Datetime("Last Seen", default=fields.Datetime.now())
    description = fields.Text("Description")  # 描述
    postcode = fields.Char("Postcode邮政编码")  # 邮政编码
    date_availability = fields.Date("Availability Date")  # 可用日期
    expected_price = fields.Float("Expected Price", digits=(14, 2))  # 期望价格
    selling_price = fields.Float("Selling Price", digits=(14, 2))  # 销售价格
    bedrooms = fields.Integer("Bedrooms", required=True)  # 卧室数
    living_area = fields.Integer("Lving Area (m2)")  # 生活区域
    facades = fields.Integer("Number of Facades")  # 门面
    garage = fields.Boolean("Garage")  # 车库
    garden = fields.Boolean("Garden")  # 花园
    garden_area = fields.Integer("Garden Area (m2)")  # 花园面积
    garden_orientation = fields.Char("Garden Orientation")  # 花园方向
    property_type_id = fields.Many2one("estate.property.type", string="Property type")

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
