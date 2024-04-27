from odoo import fields, models, api, exceptions
from decimal import Decimal
from odoo import tools
from odoo.exceptions import ValidationError


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"  # 按照id降序

    # 房产信息字段
    id = fields.Integer("Id", readonly=True)
    name = fields.Char("Name", required=True, default="Unknown")  # 房产名称
    description = fields.Text("Description")  # 描述
    postcode = fields.Char("Postcode")  # 邮政编码
    date_availability = fields.Date("Availability Date")  # 可用日期
    expected_price = fields.Float("Expected Price", digits=(14, 2))  # 预期价格
    selling_price = fields.Float("Selling Price", digits=(14, 2))  # 销售价格
    bedrooms = fields.Integer("Bedrooms", required=True)  # 卧室数量
    living_area = fields.Integer("Lving Area (m2)")  # 居住面积
    facades = fields.Integer("Number of Facades")  # 门面数量
    garage = fields.Boolean("Garage")  # 是否有车库
    garden = fields.Boolean("Garden")  # 是否有花园
    garden_area = fields.Integer("Garden Area (m2)")  # 花园面积
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[
            ("north", "North"),
            ("south", "South"),
            ("east", "East"),
            ("west", "West"),
        ],
        help="Orientation is used to info the orientation of the garden",
    )  # 花园朝向
    property_type_id = fields.Many2one(
        "estate.property.type", string="Property type"
    )  # 房产类型
    user_id = fields.Many2one(
        "res.users",
        string="Salesman",  # 销售人员
        index=True,
        default=lambda self: self.env.user,  # 默认为当前用户
    )
    partner_id = fields.Many2one(
        "res.partner", string="Buyer", index=True, copy=False
    )  # 买家
    tag_ids = fields.Many2many("estate.property.tag", string="tags")  # 标签
    offer_ids = fields.One2many(
        "estate.property.offer", "property_id", string="Offers"
    )  # 报价

    create_uid = fields.Many2one("res.users", "Created by", readonly=True)
    create_date = fields.Datetime("Created Date", readonly=True)
    write_uid = fields.Many2one("res.users", "Last Updated by", readonly=True)
    write_date = fields.Datetime("Last Updated", readonly=True)
    last_seen = fields.Datetime("Last Seen", default=fields.Datetime.now())

    # 计算字段
    total_area = fields.Integer(compute="_compute_total_area")
    best_price = fields.Float(compute="_compute_best_price")

    # 状态字段
    state = fields.Selection(
        string="State",  # 房产状态
        copy=False,
        selection=[
            ("new", "NEW"),
            ("received", "OFFER RECEIVED"),
            ("accepted", "OFFER ACCEPTED"),
            ("sold", "SOLD"),
            ("canceled", "CANCELD"),
        ],
        default="new",
    )
    status = fields.Selection(
        string="Status",  # 房产的销售状态
        selection=[("new", "NEW"), ("canceled", "CANCELED"), ("sold", "SOLD")],
        default="new",
    )

    _sql_constraints = [
        # 检查索引 预期价格与销售价格
        (
            "check_expected_price",
            "CHECK (expected_price > 0)",
            "A property expected price must be strictly positive",
        ),
        (
            "check_selling_price",
            "CHECK (selling_price) > 0",
            "A property selling price must be positive",
        ),
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

    # 计算总面积
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    # 计算最佳报价
    @api.depends("offer_ids")
    def _compute_best_price(self):
        for record in self:
            record.best_price = (
                max(record.offer_ids.mapped("price"))
                if len(record.offer_ids) > 0
                else 0
            )

    # 花园选项变化时触发的事件
    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = ""

    # 取消操作
    def action_cancel(self):
        for record in self:
            if record.status == "new":
                record.status = "canceled"
                record.state = "canceled"
                return True
            elif record.status == "sold":
                raise exceptions.UserError("Sold properties can't be cancel!")
            else:
                raise exceptions.UserError("The property has been canceled!")
        return True

    # 标记为已售出
    def action_sold(self):
        for record in self:
            if record.status == "new":
                record.status = "sold"
                record.state = "sold"
                return True
            elif record.status == "canceled":
                raise exceptions.UserError("Canceled properties can't be sold!")  # noqa:E501
            else:
                raise exceptions.UserError("The property has been sold")
        return True

    # 销售价格的数据库约束检查
    @api.constrains("selling_price", "expected_price")
    def check_selling_price(self):
        for record in self:
            min_selling_price = float(Decimal(record.expected_price) * Decimal(0.9))  # noqa:E501
            compared_result = tools.float_compare(
                record.selling_price, min_selling_price, precision_digits=3
            )
            if (
                not tools.float_is_zero(record.selling_price, precision_digits=3)  # noqa:E501
                and compared_result < 0
            ):
                raise ValidationError(
                    "The selling price cannot be lower than 90 percent of the expected price."  # noqa:E501
                )

    # 报价选项变化时触发的事件
    @api.onchange("offer_ids")
    def _onchange_state(self):
        state = "new"
        if self.status == "new":
            if tools.float_compare(self.selling_price, 0, precision_digits=3) > 0:  # noqa:E501
                state = "accepted"
            elif len(self.offer_ids) > 0:
                state = "received"
            else:
                state = self.status
        self.state = state

    # 重写删除方法，添加额外的删除条件
    def unlink(self):
        for record in self:
            if not (record.state == "new" or record.state == "canceled"):
                raise exceptions.UserError(
                    "Only new and canceled property can be deleted!"
                )
        return super().unlink()
