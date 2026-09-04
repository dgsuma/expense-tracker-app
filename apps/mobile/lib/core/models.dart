// Data models matching the API schemas.

class User {
  final String id;
  final String email;
  final String displayName;
  final String defaultCurrency;

  User({
    required this.id,
    required this.email,
    required this.displayName,
    required this.defaultCurrency,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as String,
        email: json['email'] as String,
        displayName: json['display_name'] as String,
        defaultCurrency: json['default_currency'] as String,
      );
}

class Category {
  final String id;
  final String name;
  final String kind;
  final List<Category> children;

  Category({
    required this.id,
    required this.name,
    required this.kind,
    this.children = const [],
  });

  factory Category.fromJson(Map<String, dynamic> json) => Category(
        id: json['id'] as String,
        name: json['name'] as String,
        kind: json['kind'] as String,
        children: (json['children'] as List<dynamic>? ?? [])
            .map((c) => Category.fromJson(c as Map<String, dynamic>))
            .toList(),
      );
}

class PaymentMethod {
  final String id;
  final String name;
  final String type;

  PaymentMethod({required this.id, required this.name, required this.type});

  factory PaymentMethod.fromJson(Map<String, dynamic> json) => PaymentMethod(
        id: json['id'] as String,
        name: json['name'] as String,
        type: json['type'] as String,
      );
}

class Expense {
  final String id;
  final String categoryId;
  final String? paymentMethodId;
  final String amount;
  final String currency;
  final DateTime expenseDate;
  final String description;
  final String? notes;

  Expense({
    required this.id,
    required this.categoryId,
    this.paymentMethodId,
    required this.amount,
    required this.currency,
    required this.expenseDate,
    required this.description,
    this.notes,
  });

  factory Expense.fromJson(Map<String, dynamic> json) => Expense(
        id: json['id'] as String,
        categoryId: json['category_id'] as String,
        paymentMethodId: json['payment_method_id'] as String?,
        amount: json['amount'] as String,
        currency: json['currency'] as String,
        expenseDate: DateTime.parse(json['expense_date'] as String),
        description: json['description'] as String,
        notes: json['notes'] as String?,
      );
}

class ExpensePage {
  final List<Expense> items;
  final int total;

  ExpensePage({required this.items, required this.total});

  factory ExpensePage.fromJson(Map<String, dynamic> json) => ExpensePage(
        items: (json['items'] as List<dynamic>)
            .map((e) => Expense.fromJson(e as Map<String, dynamic>))
            .toList(),
        total: json['total'] as int,
      );
}

class Summary {
  final String total;
  final int count;
  final String average;
  final String currency;

  Summary({
    required this.total,
    required this.count,
    required this.average,
    required this.currency,
  });

  factory Summary.fromJson(Map<String, dynamic> json) => Summary(
        total: json['total'] as String,
        count: json['count'] as int,
        average: json['average'] as String,
        currency: json['currency'] as String,
      );
}

class CategoryTotal {
  final String categoryName;
  final String total;
  final double percent;

  CategoryTotal({
    required this.categoryName,
    required this.total,
    required this.percent,
  });

  factory CategoryTotal.fromJson(Map<String, dynamic> json) => CategoryTotal(
        categoryName: json['category_name'] as String,
        total: json['total'] as String,
        percent: (json['percent'] as num).toDouble(),
      );
}

class TrendPoint {
  final DateTime bucket;
  final String total;

  TrendPoint({required this.bucket, required this.total});

  factory TrendPoint.fromJson(Map<String, dynamic> json) => TrendPoint(
        bucket: DateTime.parse(json['bucket'] as String),
        total: json['total'] as String,
      );
}
