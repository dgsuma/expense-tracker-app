import 'package:expense_tracker/core/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Model parsing', () {
    test('User.fromJson parses API response', () {
      final user = User.fromJson({
        'id': 'u1',
        'email': 'a@b.com',
        'display_name': 'Alice',
        'default_currency': 'EUR',
      });
      expect(user.id, 'u1');
      expect(user.email, 'a@b.com');
      expect(user.displayName, 'Alice');
      expect(user.defaultCurrency, 'EUR');
    });

    test('Category.fromJson parses nested children', () {
      final category = Category.fromJson({
        'id': 'c1',
        'name': 'Dining',
        'kind': 'expense',
        'children': [
          {'id': 'c2', 'name': 'Restaurants', 'kind': 'expense', 'children': []},
        ],
      });
      expect(category.name, 'Dining');
      expect(category.children, hasLength(1));
      expect(category.children.first.name, 'Restaurants');
    });

    test('Expense.fromJson parses a full expense', () {
      final expense = Expense.fromJson({
        'id': 'e1',
        'category_id': 'c1',
        'payment_method_id': null,
        'amount': '42.50',
        'currency': 'EUR',
        'expense_date': '2026-09-03',
        'description': 'Team lunch',
        'notes': 'with clients',
      });
      expect(expense.amount, '42.50');
      expect(expense.description, 'Team lunch');
      expect(expense.expenseDate, DateTime(2026, 9, 3));
    });

    test('ExpensePage.fromJson parses paginated results', () {
      final page = ExpensePage.fromJson({
        'items': [
          {
            'id': 'e1',
            'category_id': 'c1',
            'payment_method_id': null,
            'amount': '10.00',
            'currency': 'EUR',
            'expense_date': '2026-09-01',
            'description': 'Coffee',
            'notes': null,
          },
        ],
        'total': 1,
        'page': 1,
        'page_size': 50,
      });
      expect(page.items, hasLength(1));
      expect(page.total, 1);
    });
  });
}
