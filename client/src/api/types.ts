// Names for the generated API types. Regenerate schema.d.ts with `npm run gen:api`
// after changing the server's schemas; never edit it by hand.
import type { components } from "./schema";

type Schemas = components["schemas"];

export type AuthStatus = Schemas["AuthStatus"];
export type Meta = Schemas["Meta"];
export type Account = Schemas["AccountOut"];
export type Category = Schemas["CategoryOut"];
export type Txn = Schemas["TxnOut"];
export type TxnPage = Schemas["TxnPage"];
export type TxnPatch = Schemas["TxnPatch"];
export type Kpis = Schemas["Kpis"];
export type BalancePoint = Schemas["BalancePoint"];
export type MonthFlow = Schemas["MonthFlow"];
export type CategorySpend = Schemas["CategorySpend"];
