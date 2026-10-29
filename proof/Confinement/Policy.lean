namespace Confinement

-- Abstract, canonical path components; no host path resolution is modeled.
abbrev Path := List String

def Within (root path : Path) : Prop := ∃ suffix, path = root ++ suffix

structure Policy where
  writable : Path → Prop
  denied : Path → Prop

def AllowsWrite (policy : Policy) (path : Path) : Prop :=
  policy.writable path ∧ ¬ policy.denied path

def addWorkspace (policy : Policy) (workspace : Path) : Policy where
  writable := fun path => policy.writable path ∨ Within workspace path
  denied := policy.denied

theorem protected_subtree_remains_unwritable
    (policy : Policy) (workspace denied : Path)
    (hprotected : ∀ path, Within denied path → policy.denied path) :
    ∀ path, Within denied path →
      ¬ AllowsWrite (addWorkspace policy workspace) path := by
  intro path hwithin hwrite
  exact hwrite.2 (hprotected path hwithin)

-- Positive control: a granted, unprotected path is writable.
theorem workspace_grants_unprotected
    (policy : Policy) (workspace path : Path)
    (hwithin : Within workspace path) (hclear : ¬ policy.denied path) :
    AllowsWrite (addWorkspace policy workspace) path := by
  exact ⟨Or.inr hwithin, hclear⟩

end Confinement
