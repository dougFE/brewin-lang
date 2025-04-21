class testFramework():
  
    @staticmethod
    def debug_scope_env(self, scope_env):
        scope_count = 0
        for scope in scope_env:
            print("  " * scope_count + "-- Scope " + str(scope_count) + " --")
            for key in scope.keys():
                print("  " * (scope_count+1) + key + " = " + str(scope[key]))

    testPrograms = [
"""
func bar() {
  print("bar running");
  return false;
} 

func foo() {
  print("foo running");
  return true;
}
    
func main() {
  var a;
  var b;
  a = bar();
  b = foo();
  if (!(a && b)){
    print("over");
  }

}"""
,
"""
func main() {
  var x;
  var y;
  x = 5;
  y = x + 10;
  x = 100;
  print(y);
}
"""
,
"""
func main() {
  var x;
  var y;
  x = 10;
  y = x;
  print(x);
  print(y);
  y = y + 10;
  print(y);
}
"""
,
"""
func somefxn(x) {
  var y;
  y = 10;
  x = 8 + y;
}

func main() {
	print("hello world");
	var y;
	if (true) {
	  var x;
	  x = 5; 
	  y = 7 + x;
	}
	/* y is evaluated below so it now looks for x */
	print(y);
	/* for popping scope: */
	var z;
	z = y + 3;
	somefxn(z);
	print(z);
}
"""
,
"""
func foo(a) {
  var y;
  y = a + 5;
  print(y);
  return a;
}

func main() {
  var x;
  x = foo(5);
  print("x: ", x);
}
"""
,
"""
func main() {
print(1 || 1);
}
"""
,
"""
func main() {
var result;
result = f(g(4));
print(result);
}

func f(x) {
print("f is running");
return x + 2;
}

func g(y) {
print("g is running");
return y * y;
}
"""
,
"""
func main() {
 var a;
 var b;
 a = 10;
 b = a+1;
 b = b + a;
 print(b);
}
"""
,
"""
func foo() {
  print("F1");
  raise "except1";
  print("F3");
}

func bar() {
 try {
   print("B1");
   foo();
   print("B2");
 }
 catch "except2" {
   print("B3");
 }
 print("B4");
}

func main() {
 try {
   print("M1");
   bar();
   print("M2");
 }
 catch "except1" {
   print("M3");
 }
 catch "except3" {
   print("M4");
 }
 print("M5");
}
"""
,
"""
func bar(x) {
 print("bar: ", x);
 return x;
}

func main() {
 var a;
 a = bar("5");
 print("---");
 var b;
 b = inputi(a);
 print("---");
 print(b);
}
"""
,
"""
func zero() {
  print("zero");
  return 0;
}

func inc(x) {
 print("inc:", x);
 return x + 1;
}

func main() {
 var a;
 for (a = 0; zero() + a < 3; a = inc(a)) {
   print(a);
 }
 print("d");
}
"""
,
"""
func main() {
var x;
var y;
x = foo(3);
y = x + 10;
print(y);
print(x);
}

func foo(x) {
print("Foo");
return x;
}
"""
    ]